import flowio
from typing import List, Dict, Optional
import os
from ..models import FCSMetadata, ChannelInfo, CompensationMatrix, InstrumentInfo, PanelTable

def extract_threshold(text: Dict[str, str]) -> Optional[float]:
    """Extract FSC threshold from FCS text metadata.
    
    Priority:
    1. BD format: threshold = "FSC,15000" (key='threshold')
    2. CytoFLEX format: ch{id}th with ch{id}id=FSC, or pchid=FSC
    """
    # 1. Check BD-style 'threshold' key
    threshold_val = text.get('threshold')
    if threshold_val:
        parts = threshold_val.split(',')
        if len(parts) == 2:
            param_name, value_str = parts[0].strip(), parts[1].strip()
            if 'FSC' in param_name.upper():
                try:
                    return float(value_str)
                except ValueError:
                    pass
    
    # 2. Check CytoFLEX-style per-channel thresholds
    # Find which channel is FSC via ch{id}id or pchid
    fsc_ch_num = None
    
    # Try pchid (primary threshold parameter)
    if text.get('pchid', '').upper() == 'FSC':
        # Look for ch{X}th where ch{X}id = FSC
        for key, val in text.items():
            if key.endswith('th'):
                ch_num = key.replace('ch', '').replace('th', '')
                if ch_num.isdigit():
                    id_key = f'ch{ch_num}id'
                    if text.get(id_key, '').upper() == 'FSC':
                        try:
                            return float(val)
                        except ValueError:
                            pass
    
    # Try ch{id}id keys directly
    for key, val in text.items():
        if key.endswith('id') and val.upper() == 'FSC':
            ch_num = key.replace('ch', '').replace('id', '')
            if ch_num.isdigit():
                th_key = f'ch{ch_num}th'
                if th_key in text:
                    try:
                        return float(text[th_key])
                    except ValueError:
                        pass
    
    return None


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
                channels.append(ChannelInfo(
                    name=name,
                    label=label,
                    voltage=voltage
                ))

        # --- CytoFLEX Gain/Voltage Parsing Fallback ---
        has_voltages = any(ch.voltage is not None for ch in channels)
        if not has_voltages:
            print("Standard $PnV voltages not found. Checking CytoFLEX keywords...")
            
            # Beckman/CytoFLEX: compgainh and compgaina are identical,
            # compchh and compcha are identical.
            # Only use the 'a' (Area) version to avoid duplicate matching.
            key_names = 'compcha'
            key_gains = 'compgaina'
            
            if key_names in text and key_gains in text:
                try:
                    c_names = text[key_names].split()
                    c_gains = text[key_gains].split()
                    
                    if len(c_names) == len(c_gains):
                        print(f"Found CytoFLEX gains (Area): {list(zip(c_names, c_gains))}")
                        
                        for idx, cn in enumerate(c_names):
                            gain_val = float(c_gains[idx])
                            
                            for ch in channels:
                                # Only match Area (-A) channels
                                if not ch.name.upper().endswith("-A"):
                                    continue
                                    
                                if (ch.label and cn in ch.label) or (cn in ch.name):
                                    ch.voltage = gain_val
                                    
                except Exception as e:
                    print(f"Error parsing CytoFLEX gains: {e}")

        # 2. Extract Compensation Matrix
        compensation = None
        
        # Priority 1: Beckman/CytoFLEX 'compa' + 'compcha' (Area-only, avoids H+A duplication)
        # Beckman spillover contains both H and A channels (26x26), but H and A are
        # the same fluorochromes — only keep Area version.
        if 'compa' in text and 'compcha' in text:
            try:
                comp_names = text['compcha'].split()
                comp_vals = text['compa'].split()
                n = len(comp_names)
                expected = n * n
                
                if len(comp_vals) >= expected:
                    values_flat = [float(x) for x in comp_vals[:expected]]
                    values = []
                    for r in range(n):
                        values.append(values_flat[r*n:(r+1)*n])
                    
                    compensation = CompensationMatrix(
                        fluorochromes=comp_names,
                        values=values
                    )
                    print(f"Using Beckman compa compensation ({n}x{n})")
            except Exception as e:
                print(f"Error parsing Beckman compa: {e}")
        
        # Priority 2: Standard spillover/spill (BD, etc.)
        if compensation is None:
            spill_keys = ['spillover', '$SPILLOVER', '$SPILL', 'SPILL']
            spill_str = None
            
            for key in spill_keys:
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

        # 5. Extract FSC Threshold
        fsc_threshold = extract_threshold(text)
        
        # 6. Build PanelTable skeleton (columns and fluorophore labels)
        panel_table = build_panel_table(text, channels)
        
        print(f"DEBUG: FSC Threshold: {fsc_threshold}")
        print(f"DEBUG: PanelTable columns: {panel_table.columns if panel_table else 'None'}")

        return FCSMetadata(
            filename=filename,
            timestamp=timestamp,
            instrument=instrument,
            channels=channels,
            compensation=compensation,
            fsc_threshold=fsc_threshold,
            panel_table=panel_table
        )

    except Exception as e:
        return FCSMetadata(
            filename=filename,
            channels=[],
            error=str(e)
        )


def _extract_spill_fluorochromes(text: Dict[str, str]) -> List[str]:
    """Extract fluorochrome names from spillover/spill keywords."""
    for key in ['spillover', 'spill', '$SPILLOVER', '$SPILL']:
        if key in text:
            spill_str = text[key]
            parts = spill_str.split(',')
            if len(parts) > 0:
                try:
                    n = int(parts[0])
                    return [f.strip() for f in parts[1:n+1]]
                except (ValueError, IndexError):
                    continue
    return []


def build_panel_table(text: Dict[str, str], channels: List[ChannelInfo]) -> Optional[PanelTable]:
    """Build a PanelTable skeleton from FCS metadata.
    
    Detects fluorescence channels (excludes FSC, SSC, Time, Width)
    and extracts fluorophore labels for the second header row.
    
    Priority for fluorochrome detection:
    1. compchh/compcha (CytoFLEX clean fluorophore names)
    2. spill (BD clean names)
    3. spillover (standard FCS, may need dedup)
    4. Derive from channel names (fallback)
    """
    fluorochromes = []
    
    # 1. Try CytoFLEX compcha key (Area version — compchh is identical)
    if 'compcha' in text:
        parts = text['compcha'].split()
        if parts:
            fluorochromes = list(parts)
    elif 'compchh' in text:
        # Fallback if compcha not present
        parts = text['compchh'].split()
        if parts:
            fluorochromes = list(parts)
    
    # 2. Try spill key (BD format, clean names)
    if not fluorochromes:
        fluorochromes = _extract_spill_fluorochromes(text)
    
    # 3. Try deriving from channel names (fallback)
    if not fluorochromes:
        seen_bases = []
        for ch in channels:
            name = ch.name or ''
            if any(name.upper().startswith(p) for p in ['FSC', 'SSC']):
                continue
            if 'TIME' in name.upper() or 'WIDTH' in name.upper():
                continue
            base = name
            for suffix in ['-A', '-H', '-W']:
                if base.upper().endswith(suffix.upper()):
                    base = base[:-len(suffix)]
                    break
            if base not in seen_bases:
                seen_bases.append(base)
                fluorochromes.append(base)
    
    if not fluorochromes:
        return None
    
    columns = [f"FL{i+1}" for i in range(len(fluorochromes))]
    
    # Clean display names (strip -A, -H, -W suffixes if present)
    clean_labels = []
    for fc in fluorochromes:
        clean = fc
        for suffix in ['-A', '-H', '-W']:
            if clean.upper().endswith(suffix.upper()):
                clean = clean[:-len(suffix)]
                break
        clean_labels.append(clean)
    
    return PanelTable(
        columns=columns,
        fluorophore_labels=clean_labels,
        rows=[]
    )
