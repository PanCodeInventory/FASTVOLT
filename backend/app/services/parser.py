import flowio
from typing import List, Dict, Optional
import os
import re
from ..models import FCSMetadata, ChannelInfo, CompensationMatrix, InstrumentInfo

FLUOROPHORE_TOKENS = [
    "FITC",
    "PE",
    "APC",
    "PERCP",
    "PERCP-CY5.5",
    "PE-CY7",
    "APC-CY7",
    "BV421",
    "BV510",
    "BV605",
    "BV650",
    "BV711",
    "BV786",
    "AF488",
    "AF594",
    "AF647",
]

def infer_fluorophore(name: Optional[str], label: Optional[str]) -> Optional[str]:
    haystack = " ".join([label or "", name or ""]).upper()
    for token in FLUOROPHORE_TOKENS:
        if token in haystack:
            return token

    if name:
        base = name.split("-")[0].strip()
        return base or None

    return None

def infer_marker(label: Optional[str], fluorophore: Optional[str]) -> Optional[str]:
    if not label:
        return None

    marker = label
    if fluorophore:
        marker = re.sub(rf"\b{re.escape(fluorophore)}\b", "", marker, flags=re.IGNORECASE)
    marker = " ".join(marker.split())
    return marker or label

def parse_fcs(file_path: str, filename: str) -> FCSMetadata:
    try:
        fd = flowio.FlowData(file_path)
        text = fd.text
        
        # 1. Extract Channels and Voltages
        channels: List[ChannelInfo] = []
        channel_count = int(text.get('par', text.get('$PAR', 0)))
        
        for i in range(1, channel_count + 1):
            p_n = str(i)
            # Standard keywords: $P1N (Name), $P1S (Label/Stain), $P1V (Voltage)
            name_key = f'p{p_n}n' # flowio text keys are often normalized or accessible case-insensitively, check dict
            # Flowio text keys are case-sensitive usually, but standard is uppercase. flowio returns dict.
            
            # Helper to find key case-insensitively
            def get_val(key_suffix):
                # 1. Try lowercase normalized key (e.g., 'p1n') - common in flowio
                target_lower = f'p{p_n}{key_suffix}'.lower()
                if target_lower in text: return text[target_lower]
                
                # 2. Try standard uppercase key (e.g., '$P1N') - standard FCS
                target_upper = f'$P{p_n}{key_suffix.upper()}'
                if target_upper in text: return text[target_upper]
                
                return None

            name = get_val('n') # 'p1n' or '$P1N'
            label = get_val('s') # 'p1s' or '$P1S'
            voltage_str = get_val('v') # 'p1v' or '$P1V'
            
            voltage = None
            if voltage_str:
                try:
                    voltage = float(voltage_str)
                except ValueError:
                    pass

            if name:
                fluorophore = infer_fluorophore(name, label)
                marker = infer_marker(label, fluorophore)
                channels.append(ChannelInfo(
                    name=name,
                    label=label,
                    fluorophore=fluorophore,
                    marker=marker,
                    voltage=voltage
                ))

        # --- CytoFLEX Gain/Voltage Parsing Fallback ---
        has_voltages = any(ch.voltage is not None for ch in channels)
        if not has_voltages:
            print("Standard $PnV voltages not found. Checking CytoFLEX keywords...")
            
            # Keys found in log are lowercase: 'compchh', 'compgainh'
            for suffix in ['h', 'a']: # Height and Area (lowercase)
                key_names = f'compch{suffix}'
                key_gains = f'compgain{suffix}'
                
                if key_names in text and key_gains in text:
                    try:
                        # Values appear to be tab or space separated
                        c_names = text[key_names].split()
                        c_gains = text[key_gains].split()
                        
                        if len(c_names) == len(c_gains):
                            print(f"Found CytoFLEX gains for {suffix}: {list(zip(c_names, c_gains))}")
                            
                            for idx, cn in enumerate(c_names):
                                gain_val = float(c_gains[idx])
                                
                                # Match channel
                                for ch in channels:
                                    # ch.name might be "FL1-H" or "FITC-A"
                                    # Check suffix match (H vs A)
                                    target_suffix = "-H" if suffix == 'h' else "-A"
                                    if not ch.name.upper().endswith(target_suffix):
                                        continue
                                        
                                    # Check if gain name is in channel name or label
                                    # cn="FITC", label="CD45 FITC-H" -> Match
                                    if (ch.label and cn in ch.label) or (cn in ch.name):
                                        ch.voltage = gain_val
                                        
                    except Exception as e:
                        print(f"Error parsing CytoFLEX gains: {e}")

        # 2. Extract Spillover
        compensation = None
        
        # Log showed key is 'spillover' (lowercase, no $)
        # But we should check variants to be safe
        spill_keys = ['spillover', '$SPILLOVER', '$SPILL', 'SPILL']
        spill_str = None
        
        for key in spill_keys:
            # Check lowercase version of keys against text keys
            # or direct access if text keys are mixed
            if key in text:
                spill_str = text[key]
                break
            elif key.lower() in text:
                spill_str = text[key.lower()]
                break
        
        if spill_str:
            # Format: n, col1, col2, ..., coln, val1, val2, ...
            parts = spill_str.split(',')
            if len(parts) > 0:
                try:
                    n = int(parts[0])
                    fluorochromes = parts[1:n+1]
                    values_flat = [float(x) for x in parts[n+1:]]
                    
                    # Reshape values into matrix
                    values = []
                    for r in range(n):
                        row = values_flat[r*n : (r+1)*n]
                        values.append(row)
                    
                    compensation = CompensationMatrix(
                        fluorochromes=fluorochromes,
                        values=values
                    )
                except Exception as e:
                    print(f"Error parsing spillover string: {e}")
                    # Could log this error but continue without comp matrix

        # 4. Extract Instrument Metadata
        # Keys: $MODEL (Model), $CYTSN (Serial Number), $CYT (Instrument Name)
        # Using .get with lowercase variants or exact match logic if flowio key normalization is consistent
        
        def get_text_val(key):
            # 1. Exact match
            if key in text: return text[key]
            
            # 2. Lowercase match (e.g. '$CYT' -> '$cyt')
            if key.lower() in text: return text[key.lower()]
            
            # 3. Strip $ and lowercase (e.g. '$CYT' -> 'cyt')
            # Most flowio keys seem to be stripped of leading $
            stripped = key.lstrip('$')
            if stripped in text: return text[stripped]
            if stripped.lower() in text: return text[stripped.lower()]
            
            return None

        # 3. Extract Timestamp (Moved after helper definition)
        date_str = get_text_val('$DATE')
        time_str = get_text_val('$BTIM')
        timestamp = f"{date_str} {time_str}" if date_str and time_str else (date_str or None)

        # Instrument Logic
        raw_model = get_text_val('$MODEL')
        raw_name = get_text_val('$CYT')
        
        # If MODEL is missing or empty string, use CYT (Name) as Model
        final_model = raw_model if raw_model and raw_model.strip() else raw_name

        instrument = InstrumentInfo(
            model=final_model,
            serial_number=get_text_val('$CYTSN'),
            name=raw_name
        )
        
        print(f"DEBUG: Extracted Instrument Info: {instrument}")
        print(f"DEBUG: Extracted Timestamp: {timestamp}")

        return FCSMetadata(
            filename=filename,
            timestamp=timestamp,
            instrument=instrument,
            channels=channels,
            compensation=compensation
        )

    except Exception as e:
        return FCSMetadata(
            filename=filename,
            channels=[],
            error=str(e)
        )
