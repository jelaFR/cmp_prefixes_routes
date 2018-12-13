def sort_list_by_ipaddress(list_name):
    """
    Parse a list containing prefix parameters and sort this list by:
        1. Prefix-list name (must be the first item in the list)
        2. Prefix value (must be the second item in the list)
    :param list_name: list containing prefix parameters
    :return: list sorted with criterias above
    """
    import ipaddress
    #Get network_address from prefix, convert to decimal and sort it by prefix_list_name then prefix_value
    list_name = sorted(list_name,key=lambda
        x: (x[0],int(ipaddress.ip_address(ipaddress.ip_network(x[1]).network_address))))
    return list_name


def parse_ip_prefix_to_list(filename):
    """
    This function parse a filename looking for prefix-lists section.
    In this section, each prefix from prefix list is read and the following parameter are stored as list

    Please note that the ip is stored as decimal in order
    :param filename: file containing prefix-lists
    :return: list(prefix_list_name,prefix,prefix_mask,sequence_number,action,operator,mask)
    """
    import re
    with open(filename) as file:
        prefixes = list()
        prefix_filter = r'^ip\sprefix-list\s(?P<prefix_list>\S+)\sseq\s(?P<seq_number>\d*)\s(?P<action>\S+)\s' \
                        r'(?P<prefix>\d+.\d+.\d+.\d+/\d+)\s?(?P<operator>\S+\s\d+)?'
        for line in file:
            prefix_params = re.match(prefix_filter,line)
            if prefix_params:
                prefix_list = prefix_params.group('prefix_list')
                prefix = prefix_params.group('prefix')
                seq_number = prefix_params.group('seq_number')
                action = prefix_params.group ('action')
                operator = prefix_params.group('operator')
                prefixes.append([prefix_list,prefix,seq_number,action,operator])
    return prefixes


def ip_route_to_list(filename):
    """
    This function get the output of the "show ip route" on Cisco routers and convert it to list
    :param filename: file containing the output of "show ip route"
    :return: List with all routes and parameters
    """
    import re
    with open(filename) as file:
        ip_route = list()
        ip_route_filter = r'^(?P<method>\S+)\s+(\S+\s+)?(?P<prefix>\d+.\d+.\d+.\d+/\d+)\s+' \
                          r'(\[\d+/\d+\]\s+via\s+' \
                          r'(?P<gateway>\d+.\d+.\d+.\d+)(,\s\S+\s+(?P<next_hop>Vlan\d+))?)?' \
                          r'(is\sdirectly\sconnected,\s(?P<next_hop_connected>Vlan\d+))?'
        for line in file:
            ip_route_params = re.match (ip_route_filter, line)
            if ip_route_params:
                method =ip_route_params.group('method')
                prefix = ip_route_params.group ('prefix')
                gateway = ip_route_params.group ('gateway')
                next_hop =   ip_route_params.group ('next_hop_connected') \
                    if ip_route_params.group ('method') == "C" \
                    else ip_route_params.group ('next_hop')
                ip_route.append([method,prefix,gateway,next_hop])
    return ip_route


def is_prefix_in_list(ip_prefix, ip_route_list,operator=False, protocols_checked=['all']):
    """
    Check if a given ip prefix is in a route list
    :param ip_prefix: IP prefix to check
    :param ip_route_list: IP route list to compare with
    :param protocols_checked:
    :return: (True + list of matched prefixes and protocols) or (False if no prefix found + empty list)
    """
    import ipaddress
    import re
    match = bool()
    prefixes_matched = list()
    ip_prefix = ipaddress.ip_network(ip_prefix,True)
    for route in ip_route_list:
        route_lrn_method = route[0]
        route_prefix = ipaddress.ip_network(route[1],True)
        if route_lrn_method in protocols_checked:
            if (operator == None) or (operator == False):
                if route_prefix == ip_prefix:
                    match = True
                    prefixes_matched.append([route_lrn_method,route_prefix.exploded])
            elif "l" in str(operator):
                operator_value = int(re.sub(r'l[et]\s','', operator))
                if ip_prefix.supernet_of(route_prefix):
                    if "lt" in str(operator):
                        if route_prefix.prefixlen < operator_value:
                            match = True
                            prefixes_matched.append([route_lrn_method, route_prefix.exploded])
                    elif "le" in str(operator):
                        if route_prefix.prefixlen <= operator_value:
                            match = True
                            prefixes_matched.append([route_lrn_method, route_prefix.exploded])
            elif "g" in str(operator):
                operator_value = int(re.sub(r'g[et]\s','', operator))
                if ip_prefix.supernet_of(route_prefix):
                    if "gt" in str(operator):
                        if route_prefix.prefixlen > operator_value:
                            match = True
                            prefixes_matched.append([route_lrn_method, route_prefix.exploded])
                    elif "ge" in str(operator):
                        if route_prefix.prefixlen >= operator_value:
                            match = True
                            prefixes_matched.append([route_lrn_method, route_prefix.exploded])
    return match,prefixes_matched


def compare_prefixes_with_list(prefixes_list,routes_list):
    """
    This function compare a list of prefixes with a list of routes
    :param prefixes_list: list of prefixes
    :param routes_list: list of routes
    :return: List with all prefixes followed by matching route and protocol associated
    """
    protocols = ['B', 'D', 'C', 'S']
    prefixes_compared = list()
    for prefix_params in prefixes_list:
        ip_prefix = prefix_params[1]
        prefix_list_name = prefix_params[0]
        prefix_seq = prefix_params[2]
        prefix_operator = prefix_params[4]
        #Avoid matching default prefix with all routes
        # This will result in many matches
        if ip_prefix == "0.0.0.0/0":
            prefix_found = True
            prefixes = [["NC","NC"]]
        else:
            prefix_found,prefixes = is_prefix_in_list(ip_prefix,routes_list,prefix_operator,protocols)
        #This occurs only if a prefix has corresponding routes
        if prefix_found:
            for route_params in prefixes:
                prefixes_compared.append([prefix_list_name,ip_prefix,prefix_seq,prefix_operator,route_params[0],route_params[1]])
        else:
            prefixes_compared.append ([prefix_list_name, ip_prefix,prefix_seq,prefix_operator, "None", "None"])
    return prefixes_compared


def list_to_xlsx(list,outfile):
    import os
    import xlsxwriter
    # Check if file exists and remove previous one
    if os.path.isfile(out_file):
        os.remove(out_file)
    # Create an excel workbook
    workbook = xlsxwriter.Workbook(outfile)
    worksheet = workbook.add_worksheet ("Prefixes")
    header_cell = workbook.add_format ({'bold': True, 'font_color': 'blue', 'shrink': True})
    worksheet.write (0, 0, 'PL_name',header_cell)
    worksheet.write (0, 1, 'IP_prefix',header_cell)
    worksheet.write (0, 2, 'operator', header_cell)
    worksheet.write (0, 3, 'seq',header_cell)
    worksheet.write (0, 4, 'connected',header_cell)
    worksheet.write (0, 5, 'static',header_cell)
    worksheet.write (0, 6, 'EIGRP',header_cell)
    worksheet.write (0, 7, 'OSPF',header_cell)
    worksheet.write (0, 8, 'BGP',header_cell)
    row = 1
    for prefix_list_name,prefix,seq,operator,protocol,route in (list):
        worksheet.write(row,0,prefix_list_name)
        worksheet.write(row, 1, prefix)
        worksheet.write (row, 2, operator)
        worksheet.write (row, 3, seq)
        if ("NC" not in protocol) and ("None" not in protocol):
            col = 8 if protocol == "B" else \
                7 if protocol == "O" else \
                6 if protocol == "D" else \
                5 if "S" in protocol else \
                4 if protocol == "C" else \
                print ("Error with the following prefix:", prefix)
            worksheet.write (row, col, route)
        row += 1
    workbook.close ()


if __name__ == "__main__":
    #Vars
    pl_filename = r"PATH_TO_PREFIX_LISTS"
    ipr_filename = r"PATH_TO_SHIP_ROUTE"
    out_file = r'OUT_FILE'

    #Parse prefix-list and sort by IP
    prefixes_list = parse_ip_prefix_to_list(pl_filename)
    prefixes_list = sort_list_by_ipaddress(prefixes_list)

    #Parse show ip route
    routes_list = ip_route_to_list(ipr_filename)
    routes_list = sort_list_by_ipaddress(routes_list)

    #Compate prefixes to ip_routes
    compare_result = compare_prefixes_with_list(prefixes_list, routes_list)

    #Write output list to excel file
    list_to_xlsx(compare_result,out_file)