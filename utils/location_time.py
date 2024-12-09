

import requests

def get_location_from_ip(ip_address):
    # Check if the IP is a local address
    if ip_address.startswith("127.") or ip_address.startswith("10.") or ip_address.startswith("192.168."):
        return "Local Network"  # For local or private IP addresses, return a default value
    
    try:
        response = requests.get(f"https://ipinfo.io/{ip_address}/json")
        response.raise_for_status()  # Check if the request was successful
        data = response.json()
        location = data.get('loc', 'Unknown')  # 'loc' typically returns latitude,longitude
        return location
    except requests.RequestException as e:
        print(f"Error retrieving location for IP {ip_address}: {e}")  # Debug information
        return 'Unknown'