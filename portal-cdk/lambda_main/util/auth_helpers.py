def get_ip_and_country(event):
    ip_address_with_port = event.get("headers", {}).get(
        "cloudfront-viewer-address", "0.0.0.0"
    )
    country_code = event.get("headers", {}).get("cloudfront-viewer-country", "ZZ")

    ip_address = ip_address_with_port.rsplit(":", 1)[0]
    return (ip_address, country_code)