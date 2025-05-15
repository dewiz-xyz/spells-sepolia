#!/usr/bin/env python3
"""
Contract verification script for Sky Protocol spells on Etherscan.
This script verifies both the DssSpell and DssSpellAction contracts.
"""
import os
import sys
import subprocess
import time
import re
import json
import requests
from datetime import datetime

api_key = ''
rpc_url = ''

try:
    api_key = os.environ['ETHERSCAN_API_KEY']
except KeyError:
    print('''  You need an Etherscan API key to verify contracts.
  Create one at https://etherscan.io/myapikey\n
  Then export it with `export ETHERSCAN_API_KEY=xxxxxxxx'
''')
    exit()

try:
    rpc_url = os.environ['ETH_RPC_URL']
except KeyError:
    print('''  You need a valid ETH_RPC_URL.
  Get a public one one at https://chainlist.org/ or provide your own
  Then export it with `export ETHERSCAN_API_KEY=xxxxxxxx'
''')
    exit()

if len(sys.argv) not in [3, 4]:
    print('''usage:\n
./verify.py <contractname> <address> [constructorArgs]
''')
    exit()

spell_contract_name = sys.argv[1]
spell_contract_address = sys.argv[2]
print(
    f'Attempting to verify contract {spell_contract_name} at address {spell_contract_address}...')

if len(spell_contract_address) != 42:
    exit('malformed address')
spell_constructor_arguments = ''
if len(sys.argv) == 4:
    spell_constructor_arguments = sys.argv[3]

print(f'DssSpell address: {spell_contract_address}')

module = 'contract'
action = 'verifysourcecode'
code_format = 'solidity-single-file'

flatten_output_path = 'out/flat.sol'
subprocess.run(['forge', 'flatten', 'src/DssSpell.sol',
               '--output', flatten_output_path])


print('Obtaining chain ID... ')
cast_chain_id = subprocess.run(['cast', 'chain-id'], capture_output=True)
chain_id = cast_chain_id.stdout.decode('utf-8')[:-1]
print("CHAIN_ID: " + chain_id)


def get_library_address():
    """
    Looks for the DssExecLib address in foundry.toml
    """
    try:
        config = open('foundry.toml').read()
        result = re.search(r':DssExecLib:(0x[0-9a-fA-F]{40})', config)
        library_address = result.group(1)
        return library_address
    except FileNotFoundError:
        raise ValueError('No foundry.toml found')
    except AttributeError:
        raise ValueError('No DssExecLib configured in foundry.toml')
    except Exception as e:
        raise ValueError(str(e))


library_name = 'DssExecLib'
library_address = ''

try:
    library_address = get_library_address()
    print(f'Using library {library_name} at address {library_address}')
except ValueError as e:
    print(e)
    print('WARNING: Assuming this contract uses no libraries')


def send_etherscan_api_request(params, data):
    """
    Sends the verification request to the Etherscan API
    """

    url = 'https://api.etherscan.io/v2/api'
    headers = {
        'User-Agent': ''
    }

    print('Sending verification request...')
    response = requests.post(url, headers=headers, params=params, data=data)
    payload = {}
    try:
        payload = json.loads(response.text)
    except json.decoder.JSONDecodeError:
        print(response.text, file=sys.stderr)
        raise Exception('Error: Etherscan responded with invalid JSON.')
    return payload


def verify_contract(name=None, address=None, input_path=None, output_path=None):
    document = ''
    content = {}
    try:
        document = open(output_path)
        content = json.load(document)
    except FileNotFoundError:
        raise Exception('run forge build first')
    except json.decoder.JSONDecodeError:
        raise Exception('run forge build again')

    metadata = content['metadata']
    compiler_version = 'v' + metadata['compiler']['version']
    evm_version = metadata['settings']['evmVersion']
    optimizer_enabled = metadata['settings']['optimizer']['enabled']
    optimizer_runs = metadata['settings']['optimizer']['runs']
    license_name = metadata['sources'][input_path]['license']
    license_numbers = {
        'GPL-3.0-or-later': 5,
        'AGPL-3.0-or-later': 13
    }
    license_number = license_numbers[license_name]

    code = ''
    with open(flatten_output_path, 'r', encoding='utf-8') as code_file:
        code = code_file.read()

    params = {
        'chainid': chain_id,
    }

    data = {
        'apikey': api_key,
        'module': module,
        'action': action,
        'contractaddress': address,
        'sourceCode': code,
        'codeFormat': code_format,
        'contractName': name,
        'compilerversion': compiler_version,
        'optimizationUsed': '1' if optimizer_enabled else '0',
        'runs': optimizer_runs,
        'constructorArguements': spell_constructor_arguments,
        'evmversion': evm_version,
        'licenseType': license_number,
        'libraryname1': library_name,
        'libraryaddress1': library_address,
    }

    verify_response = send_etherscan_api_request(params, data)

    while 'locate' in verify_response['result'].lower():
        print(verify_response['result'])
        print('Waiting for 15 seconds for the network to update...')
        time.sleep(15)
        verify_response = send_etherscan_api_request(params, data)

    if verify_response['status'] != '1' or verify_response['message'] != 'OK':
        print('Error: ' + verify_response['result'])
        if 'already verified' not in verify_response['result'].lower():
            raise Exception('Failed to verify')
        else:
            return

    print('Sent verification request with guid ' + verify_response['result'])

    guid = verify_response['result']

    check_response = {}

    while check_response == {} or 'pending' in check_response['result'].lower():

        if check_response != {}:
            print(check_response['result'])
            print('Waiting for 15 seconds for Etherscan to process the request...')
            time.sleep(15)

        check_response = send_etherscan_api_request(params=params, data={
            'apikey': api_key,
            'module': module,
            'action': 'checkverifystatus',
            'guid': guid,
        })

    if check_response['status'] != '1' or check_response['message'] != 'OK':
        print('Error: ' + check_response['result'])
        if 'already verified' not in check_response['result'].lower():
            log_name = 'verify-{}.log'.format(datetime.now().timestamp())
            log = open(log_name, 'w')
            log.write(code)
            log.close()
            print(f'log written to {log_name}')
            raise Exception('Failed to get verification status')
        else:
            return


etherscan_subdomains = {
    '1': '',
    '11155111': 'sepolia.'
}

verify_contract(
    name=spell_contract_name,
    address=spell_contract_address,
    input_path='src/DssSpell.sol',
    output_path='out/DssSpell.sol/DssSpell.json',
)

print('Spell Contract verified at https://{0}etherscan.io/address/{1}#code'.format(
    etherscan_subdomains[chain_id],
    spell_contract_address
))


cast_call_actions = subprocess.run(['cast', 'call', spell_contract_address, 'action()(address)'], capture_output=True, env=os.environ | {
    'ETH_GAS_PRICE': '0',
    'ETH_PRIO_FEE': '0'
})
action_contract_name = "DssSpellAction"
action_contract_address = cast_call_actions.stdout.decode('utf-8')[:-1]

print(f'Spell DssAction address: {action_contract_address}')

verify_contract(
    name=action_contract_name,
    address=action_contract_address,
    input_path='src/DssSpell.sol',
    output_path='out/DssSpell.sol/DssSpellAction.json',
)

print('Action Contract verified at https://{0}etherscan.io/address/{1}#code'.format(
    etherscan_subdomains[chain_id],
    action_contract_address
))
