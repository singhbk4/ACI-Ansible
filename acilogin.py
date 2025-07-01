import requests
import csv
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

APIC_URL = "https://<APIC_IP>"
USERNAME = "<your_username>"
PASSWORD = "<your_password>"

def login(apic_url, username, password):
    url = f"{apic_url}/api/aaaLogin.json"
    payload = {
        "aaaUser": {
            "attributes": {
                "name": username,
                "pwd": password
            }
        }
    }
    session = requests.Session()
    resp = session.post(url, json=payload, verify=False)
    if resp.status_code == 200:
        print("Login successful")
        return session
    else:
        print("Login failed:", resp.text)
        return None

def create_tenant(session, apic_url, tenant_name):
    url = f"{apic_url}/api/node/mo/uni/tn-{tenant_name}.json"
    payload = {
        "fvTenant": {
            "attributes": {
                "name": tenant_name
            }
        }
    }
    session.post(url, json=payload, verify=False)

def create_vrf(session, apic_url, tenant_name, vrf_name):
    url = f"{apic_url}/api/node/mo/uni/tn-{tenant_name}/ctx-{vrf_name}.json"
    payload = {
        "fvCtx": {
            "attributes": {
                "name": vrf_name
            }
        }
    }
    session.post(url, json=payload, verify=False)

def create_app_profile(session, apic_url, tenant_name, app_profile):
    url = f"{apic_url}/api/node/mo/uni/tn-{tenant_name}/ap-{app_profile}.json"
    payload = {
        "fvAp": {
            "attributes": {
                "name": app_profile
            }
        }
    }
    session.post(url, json=payload, verify=False)

def create_bd(session, apic_url, tenant_name, bd_name, vrf_name):
    url = f"{apic_url}/api/node/mo/uni/tn-{tenant_name}/BD-{bd_name}.json"
    payload = {
        "fvBD": {
            "attributes": {
                "name": bd_name
            },
            "children": [
                {
                    "fvRsCtx": {
                        "attributes": {
                            "tnFvCtxName": vrf_name
                        }
                    }
                }
            ]
        }
    }
    session.post(url, json=payload, verify=False)

def create_epg(session, apic_url, tenant_name, app_profile, epg_name, bd_name):
    url = f"{apic_url}/api/node/mo/uni/tn-{tenant_name}/ap-{app_profile}/epg-{epg_name}.json"
    payload = {
        "fvAEPg": {
            "attributes": {
                "name": epg_name
            },
            "children": [
                {
                    "fvRsBd": {
                        "attributes": {
                            "tnFvBDName": bd_name
                        }
                    }
                }
            ]
        }
    }
    session.post(url, json=payload, verify=False)

if __name__ == "__main__":
    session = login(APIC_URL, USERNAME, PASSWORD)
    if not session:
        exit(1)

    # Read CSV and collect unique constructs
    tenants = set()
    vrfs = set()
    app_profiles = set()
    bds = []
    epgs = []

    with open("aci_vars.csv", newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            tenants.add(row["tenant"])
            vrfs.add((row["tenant"], row["vrf"]))
            app_profiles.add((row["tenant"], row["app_profile"]))
            bds.append({"tenant": row["tenant"], "bd": row["bd"], "vrf": row["vrf"]})
            epgs.append({"tenant": row["tenant"], "app_profile": row["app_profile"], "epg": row["epg"], "bd": row["bd"]})

    # Create unique tenants
    for tenant in tenants:
        create_tenant(session, APIC_URL, tenant)

    # Create unique VRFs
    for tenant, vrf in vrfs:
        create_vrf(session, APIC_URL, tenant, vrf)

    # Create unique App Profiles
    for tenant, app_profile in app_profiles:
        create_app_profile(session, APIC_URL, tenant, app_profile)

    # Create BDs (may be duplicates if in CSV, but ACI is idempotent)
    for bd in bds:
        create_bd(session, APIC_URL, bd["tenant"], bd["bd"], bd["vrf"])

    # Create EPGs
    for epg in epgs:
        create_epg(session, APIC_URL, epg["tenant"], epg["app_profile"], epg["epg"], epg["bd"])