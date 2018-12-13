# cmp_prefixes_routes
This script compare a running-config containing prefix-lists to a file containing "show ip route" output.
For now, this is only tested on ISR routers and Catalyst 4500x (IOS-XE).

Please change the following vars in order to let the magic happend ;)
    pl_filename = r"PATH_TO_PREFIX_LISTS"
      -> This is a simple output from show running-config
    ipr_filename = r"PATH_TO_SHIP_ROUTE"
      -> This is the output of "show ip route"
    out_file = r'OUT_FILE'
      -> This is the full path (including filename) to the excel file (.xlsx)
