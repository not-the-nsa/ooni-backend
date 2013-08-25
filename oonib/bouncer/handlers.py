import json 
import random
import yaml
from oonib import errors as e
from oonib.handlers import OONIBHandler
from oonib import config

class Bouncer(object):
    def __init__(self):
        self.knownHelpers = {}
        self.updateKnownHelpers()
        self.updateKnownCollectors()
        
    def updateKnownHelpers(self):
        with open(config.main.bouncer_file) as f:
            bouncerFile = yaml.safe_load(f)
            for collectorName, helpers in bouncerFile['collector'].items():
                for helperName, helperAddress in helpers['test-helper'].items():
                    if helperName not in self.knownHelpers.keys():
                        self.knownHelpers[helperName] = []
                  
                    self.knownHelpers[helperName].append({
                        'collector-name': collectorName,
                        'helper-address': helperAddress
                    })

    def updateKnownCollectors(self):
        """
        Returns the list of all known collectors
        """
        self.knownCollectors = []
        with open(config.main.bouncer_file) as f:
            bouncerFile = yaml.safe_load(f)
            for collectorName, helpers in bouncerFile['collector'].items():
                if collectorName not in self.knownCollectors:
                    self.knownCollectors.append(collectorName)

    def getHelperAddresses(self, helper_name):
        """
        Returns a dict keyed on the collector address of known test helpers.
        example:
         {
            'httpo://thirteenchars1.onion': '127.0.0.1',
            'httpo://thirteenchars2.onion': '127.0.0.2',
            'httpo://thirteenchars3.onion': '127.0.0.3'
         }
        """
        try:
            helpers = self.knownHelpers[helper_name]
        except KeyError:
            raise e.NoHelperFound
        
        helpers_dict = {}
        for helper in helpers:
            helpers_dict[helper['collector-name']] = helper['helper-address']

        return helpers_dict
    
    def queryHelper(self, requested_helper=None):
        """
        Returns a dict with the collector and associated helper that was requested.
        If no helper was specified, then a random collector shall be returned.

        Example:
        Client sends:
        {
          'test-helper': 'test_helper_name'
        }

        The bouncer replies:
        {
          'test-helper': 'address:port',
          'collector': 'httpo://collector.onion'
        }

        A client may also send:
        {
          'test-collector': 'net test name'
        }

        The bouncer replies:
        {
          'collector': 'httpo://collector.onion'
        }
        """
        result = {}
        if not requested_helper:
            result['collector'] = random.choice(self.knownCollectors)
            return result

        try:
            for collector, helper_address in random.choice(self.getHelperAddresses(requested_helper)):
                result['collector'] = collector
                result['test-helper'] = helper_address
                return result

        except IndexError:
            return {}

class BouncerQueryHandler(OONIBHandler):
    def initialize(self):
        self.bouncer = Bouncer()

    def updateKnownHelpers(self):
        with open(config.main.bouncer_file) as f:
            bouncerFile = yaml.safe_load(f)
            for collectorName, helpers in bouncerFile['collector'].items():
                for helperName, helperAddress in helpers['test-helper'].items():
                    if helperName not in self.knownHelpers.keys():
                        self.knownHelpers[helperName] = []
                  
                    self.knownHelpers[helperName].append({
                        'collector-name': collectorName,
                        'helper-address': helperAddress
                    })

    def post(self):
        try:
            query = json.loads(self.request.body)
        except ValueError:
            raise e.InvalidRequest

        # either return the requested helper, a random collector, or {}
        # XXX: presently we don't care about the test-id, so we just
        # return a random collector from our collection if the client
        # didn't ask for a specific helper.
        requested_helper = query.get('test-helper', None)
        self.write(self.bouncer.queryHelper(requested_helper))
