import configparser
import collections
import sys
from pathlib import Path
import re
import requests


class CustomConfigParser:
    def __init__(self):
        self.settings = {}

    def _config_rules(self, CONFIG_PATH):
        if self.settings['windows_domain_controller'] == "0" and self.settings['windows_server_join_domain'] == "1":
            print("ERROR - with configuration file at {0} 'windows_server_join_domain' must be set to '0' "
                  "if the number of 'windows_domain_controller' is set to '0'".format(CONFIG_PATH))
            sys.exit(1)

        # lets load the dsp certificate if enabled
        if self.settings['install_dsp'] == "1":
            dsp_client_cert_path = Path(self.settings['dsp_client_cert_path'])
            if dsp_client_cert_path.is_file():
                print("attack_range loaded dsp client certificate from path: {0}".format(dsp_client_cert_path.absolute()))
                self.settings['dsp_client_cert_path'] = str(dsp_client_cert_path.absolute())
            else:
                print("ERROR - with configuration file at: {0}, failed to load dsp client certificate \
                        from path: {1} and install_dsp is enabled".format(CONFIG_PATH, dsp_client_cert_path))
                sys.exit(1)

        key_name_regex = re.compile('[@!#$%^&*_=().\' <>?/\|}{~:]')
        if (key_name_regex.search(self.settings['key_name']) != None):
            print("ERROR - with configuration file at: {0}, no special characters, underscores, spaces, no single quotes allowed in key_name: {1}".format(
                CONFIG_PATH, self.settings['key_name']))
            sys.exit(1)

        range_name_regex = re.compile('[@!#$%^&*()\' <>?/\|}{~:]')
        if (range_name_regex.search(self.settings['range_name']) != None):
            print("ERROR - with configuration file at: {0}, no special characters, spaces, single quotes allowed in range_name: {1}".format(
                CONFIG_PATH, self.settings['range_name']))
            sys.exit(1)

        if '0.0.0.0/0' in self.settings['ip_whitelist']:
            print("WARNING - with configuration file at: {0}, the attack range will be public and open to the world, it is recommended that users secure attack_range servers by whitelisting only the public IP address in this format: ip_whitelist= <X.X.X.X>/32".format(CONFIG_PATH))

        # Check if Phantom Credentials work
        if self.settings['phantom_server'] == "1":
            base_url = "https://repo.phantom.us/phantom/4.10/product"
            r = requests.get(base_url, auth=(self.settings['phantom_community_username'], self.settings['phantom_community_password']))
            if r.status_code == 200:
                print("Confirmed valid Phantom Community Credentials")
            else:
                print("Unable to authenticate to Phantom Community, check your credentials")
                sys.exit(1)


        # Check for disallowed BOTS dataset combinations or syntax
        if self.settings['splunk_bots_dataset'] != '0':
            allowed_bots_data_sets = ('1', '1a', '2', '2a', '3')
            requested_bots_data_sets = [x.strip() for x in str(
                self.settings['splunk_bots_dataset']).split(',')]
            for requested_bots_dataset in requested_bots_data_sets:
                if requested_bots_dataset not in allowed_bots_data_sets:
                    print("ERROR - in configuration file: {0}, unknown BOTS dataset identifier: {1}".format(
                        CONFIG_PATH, requested_bots_dataset))
                    sys.exit(1)

            if '1' in requested_bots_data_sets and '1a' in requested_bots_data_sets:
                print(
                    "ERROR - in configuration file: {0}, cannot include datasets '1' and '1a'".format(CONFIG_PATH))
                sys.exit(1)

            if '2' in requested_bots_data_sets and '2a' in requested_bots_data_sets:
                print(
                    "ERROR - in configuration file: {0}, cannot include datasets '2' and '2a'".format(CONFIG_PATH))
                sys.exit(1)

            if bool(re.search(r"\s", self.settings['splunk_bots_dataset'])):
                print(
                    "ERROR - in configuration file: {0}, cannot include whitespace in BOTS data set config directive.".format(CONFIG_PATH))
                sys.exit(1)

    def load_conf(self, CONFIG_PATH):
        """Provided a config file path and a collections of type dict,
        will return that collections with all the settings in it"""

        config = configparser.RawConfigParser()
        config.read(CONFIG_PATH)
        for section in config.sections():
            for key in config[section]:
                try:
                    self.settings[key] = config.get(section, key)
                except Exception as e:
                    print(
                        "ERROR - with configuration file at {0} failed with error {1}".format(CONFIG_PATH, e))
                    sys.exit(1)
        self._config_rules(CONFIG_PATH)

        return self.settings
