class yamahaDefinitions():
    
    systemStates=["config", "device_status", "device_features", "event_status", "power", "misc", "network", "vt"]
    mainZoneStates=["zone_config", "basic_status", "adrc", "decoder_sel"]
    
    itemStates={
                "device_status": '<YAMAHA_AV cmd="GET"><System><Power_Control><Power>GetParam</Power></Power_Control></System></YAMAHA_AV>',
                "device_features": '<YAMAHA_AV cmd="GET"><System><Feature_Existence>GetParam</Feature_Existence></System></YAMAHA_AV>',
                "event_status": '<YAMAHA_AV cmd="GET"><System><Misc><Event><Notice>GetParam</Notice></Event></Misc></System></YAMAHA_AV>',
                "config": '<YAMAHA_AV cmd="GET"><System><Config>GetParam</Config></System></YAMAHA_AV>',
                "power": '<YAMAHA_AV cmd="GET"><System><Power_Control><Power>GetParam</Power></Power_Control></System></YAMAHA_AV>',
                "misc": '<YAMAHA_AV cmd="GET"><System><Misc>GetParam</Misc></System></YAMAHA_AV>',
                "network": '<YAMAHA_AV cmd="GET"><System><Misc><Network><Info>GetParam</Info></Network></Misc></System></YAMAHA_AV>',
                "vt": '<YAMAHA_AV cmd="GET"><System><Input_Output><Volume_Trim>GetParam</Volume_Trim></Input_Output></System></YAMAHA_AV>',

                "zone_config":'<YAMAHA_AV cmd="GET"><Main_Zone><Config>GetParam</Config></Main_Zone></YAMAHA_AV>',
                "basic_status": '<YAMAHA_AV cmd="GET"><Main_Zone><Basic_Status>GetParam</Basic_Status></Main_Zone></YAMAHA_AV>',
                "adrc": '<YAMAHA_AV cmd="GET"><Main_Zone><Sound_Video><Adaptive_DRC>GetParam</Adaptive_DRC></Sound_Video></Main_Zone></YAMAHA_AV>',
                "decoder_sel":' <YAMAHA_AV cmd="GET"><Main_Zone><Input><Decoder_Sel><Current>GetParam</Current></Decoder_Sel></Input></Main_Zone></YAMAHA_AV>',

                "zone2_status": '<YAMAHA_AV cmd="GET"><Zone_2><Basic_Status>GetParam</Basic_Status></Zone_2></YAMAHA_AV>',
                "tuner_status": '<YAMAHA_AV cmd="GET"><Tuner><Play_Info>GetParam</Play_Info></Tuner></YAMAHA_AV>',
                "tuner_presets": '<YAMAHA_AV cmd="GET"><Tuner><Play_Control><Preset><Data>GetParam</Data></Preset></Play_Control></Tuner></YAMAHA_AV>',
                "pandora_status": '<YAMAHA_AV cmd="GET"><Pandora><Play_Info>GetParam</Play_Info></Pandora></YAMAHA_AV>',
                "pandora_station": '<YAMAHA_AV cmd="GET"><Pandora><List_Info>GetParam</List_Info></Pandora></YAMAHA_AV>',
                "pc_status": '<YAMAHA_AV cmd="GET"><PC><Play_Info>GetParam</Play_Info></PC></YAMAHA_AV>'

    }

    allsurroundmodes=[
                "Hall in Munich", 
                "Hall in Vienna", 
                "Hall in Amsterdam", 
                "Church in Freiburg", 
                "Church in Royaumont", 
                "Chamber", 
                "Village Vanguard", 
                "Warehouse Loft", 
                "Cellar Club",
                "The Roxy Theatre",
                "The Bottom Line", 
                "Sports", 
                "Action Game", 
                "Roleplaying Game", 
                "Music Video", 
                "Recital/Opera", 
                "Standard", 
                "Spectacle", 
                "Sci-Fi", 
                "Adventure",
                "Drama",
                "Mono Movie",
                "2ch Stereo",
                "7ch Stereo",
                "9ch Stereo",
                "Straight Enhancer",
                "7ch Enhancer",
                "Surround Decoder"
    ]