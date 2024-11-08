#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script can be used to talk to the SingleQuantum Retina WebSQ.

This project is licensed under the terms of the MIT license.
Copyright (c) 2023 Single Quantum B. V. and Hielke Walinga
"""
import json
import sys
import time
import uuid
from functools import reduce
from math import floor

# Python 2/3 compatibility imports
try:
    from urllib.parse import urlencode, urlsplit, urlunsplit
    from urllib.request import Request, urlopen
except ImportError:
    from urllib import urlencode

    from urllib2 import Request, urlopen
    from urlparse import urlsplit, urlunsplit


CU_INTTIME = 10  # The time (ms) of a cu (channel unit) cycle.


def merge(a, b, path=None):
    """Merges dictionary `b` recursively into dictionary `a` keeping all deeply nested data.

    Thus it won't simply overwrite a value at a key if that value is a dictionary again.
    It raises an Exception when `b` contains a value at a place where `a` has a nested data structure.
    Very similar to lodash.merge https://docs-lodash.com/v4/merge/ which is used by the websq as well.

    Parameters
    ----------
    a : dict
        Target dictionary.
    b : dict
        Dictionary to extract new values from.
    path : list
        Keeps track of previous values when going nested during recursion.

    Returns
    -------
    dict
        The `a` dictionary with new values from `b`.
    """
    path = path or []  # Initialize recursion for better error message.

    for key in b:
        if isinstance(a.get(key), dict):
            if not isinstance(b.get(key), dict):
                # Will not merge a value when there is a nested data structure already in place.
                raise Exception('Conflict at ' + '.'.join(path + [str(key)]))

            # Here the dictionaries are recursively merged keeping all the deeply nested data.
            merge(a[key], b[key], path + [str(key)])
            continue

        # b takes precendence
        a[key] = b[key]

    return a


class JsonRpc(object):
    """This class takes the `api_url` and then can be used to send
    standard HTTP requests with `request` or json rpc requests with `jsonrpc`.
    """

    def __init__(self, api_url, jsonrpc_version='2.0'):
        """Initialize a JsonRpc class.

        Parameters
        ----------
        api_url : str
            The URL of the api endpoint.
        jsonrpc_version : str
            The JSON RPC version this endpoint uses.
        """
        self.api_url = api_url
        self.jsonrpc_version = jsonrpc_version

    def request(self, params=None, payload=None):
        """Perform a GET HTTP request, if given a payload a POST.

        Parameters
        ----------
        params : list, optional
            A list of parameters added to the `self.api_url`.
        payload : dict, optional
            If provided sends `payload` as JSON with a POST.

        Returns
        -------
        dict
            Returns the result as a dict converted from the json received.

        Raises
        ------
        AssertionError
            Raises an assertion error when the HTTP response code is not 200.
        """
        headers = {}
        request_data = None
        headers["Accept"] = "application/json"
        target = self.api_url

        if params:
            target += "?" + urlencode(params, doseq=True, safe="/")

        if payload:
            headers["Content-Type"] = "application/json; charset=UTF-8"
            request_data = json.dumps(payload).encode()

        http_request = Request(target, data=request_data, headers=headers)
        http_response = urlopen(http_request)

        content_charset = "utf-8"  # default
        if hasattr(http_response, 'status'):  # Python3 only
            assert http_response.status == 200, "Got HTTP " + str(http_response.status) + " with " \
                + http_response.read().decode(content_charset)
            content_charset = http_response.headers.get_content_charset(content_charset)

        body = http_response.read().decode(content_charset)

        return json.loads(body)

    def jsonrpc(self, method, **params):
        """Makes a JSON RPC request to the `self.api_url`.

        Parameters
        ----------
        method : str
            The name of the method you want to call.
        params : list[str], optional
            The list of parameters provided to that function.

        Returns
        -------
        dict with keys as str
            The result of the function as a dictionary.

        Raises
        ------
        AssertionError
            If the request fails are the method does not exists.
        """
        identifier = str(uuid.uuid4())
        payload = {
            'method': method,
            'params': params or [],
            'jsonrpc': self.jsonrpc_version,
            'id': identifier,
        }
        response_data = self.request(payload=payload)
        assert response_data['jsonrpc'], "No jsonrpc response"
        assert response_data['id'] == identifier, "Incorrect identifier in response"

        if 'result' in response_data:
            return response_data['result']
        else:
            raise ValueError(response_data['error']['data']['message'])


class WebSQController(JsonRpc):
    """This class can send requests to the websq via the JSON RPC protocol.
    Set the `domain` of the websq in the initialization.

    A lot of funtionality requires the settings object.
    Function that rely on the settings object can be passed settings as a keyword
    argument to prevent retrieving the settings object multiple times.

    Some functionality accepts the selectedCus parameter.
    This parameter determines from what locations you pull the data.
    The selectedCus is a list of integers which are the ranks of the detectors.
    The rankMap specifies the exact location of these detectors.
    If this is not set (or None) all locations are returned.

    For some functionality you can provide the `asLists` argument.
    Setting this to True gives your data as lists as opposed to a list of dicts.
    """

    def __init__(self, domain=None, api_url=None, cu_inttime=CU_INTTIME):
        """Initialize a WebSQController class

        Parameters
        ----------
        domain : str
            The domain the websq controller can be accessed on.
            We set the /api path onto this domain name.
        api_url : str
            Instead of the domain, you can also specify the api_url directly
            with the correct path to the JSON RPC endpoint.
        cu_inttime : float
            The duration (ms) a cu (channel unit) cycle.
            The default is 10ms for Retina and 15ms for the backport.
        """
        res = urlsplit(domain)
        api_url = api_url or urlunsplit((res.scheme, res.netloc, '/api', '', ''))
        self.cu_inttime = cu_inttime
        super(WebSQController, self).__init__(api_url)

    def setSettings(self, **params):
        return self.jsonrpc('setSettings', **params)

    def setNetworkSettings(self, **params):
        return self.jsonrpc('setNetworkSettings', **params)

    def setHostName(self, hostname):
        return self.jsonrpc("setHostname", hostname=hostname)

    def startRecording(self, channels=[]):
        """Turns on recording mode, the data recorded will be returned by the stopRecording command"""
        if len(channels) == 0:
            channels = self.getAllRanks()
        return self.jsonrpc("startRecording", channels=channels)

    def stopRecording(self):
        """Stops recording mode, will return the data which was collected while recording."""
        return self.jsonrpc("stopRecording")

    def getChannelConfiguration(self, name, channelLoc=None, selectedCus=None, settings=None):
        """ Gets the channel configuration for the quantity "name"

        Parameters
        ----------
        channelLoc : dict, optional
            A dictionary that maps the rank of a cu to the location in terms of [mcuId, cuId]
            for which to perform this action. If not provided, use all of them.
        selectedCus : list of int, optional
            The list of ranks of the detectors (channel units)
            for which to perform this action. If not provided, use all of them.
        settings : dict, optional
            The `settings` will be retrieved or can be provided with keyword argument `settings`.

        Returns
        -------
        list
            a list containing the values read for the requested quantity

        """
        settings = settings or self.getSettings()
        channelLoc = channelLoc or self.getChannelLoc(selectedCus, settings)
        values = []
        for (mcuId, cuId) in channelLoc.values():
            mcuId, cuId = str(mcuId), str(cuId)
            values.append(self.getChannelInformationByLoc(mcuId, cuId, "configuration", settings=settings)[name])
        return values

    def setChannelConfiguration(self, name, value, channelLoc=None, selectedCus=None, settings=None):
        """ Sets the channel configuration name to value.

        Parameters
        ----------
        channelLoc : dict, optional
            A dictionary that maps the rank of a cu to the location in terms of [mcuId, cuId]
            for which to perform this action. If not provided, use all of them.
        selectedCus : list of int, optional
            The list of ranks of the detectors (channel units)
            for which to perform this action. If not provided, use all of them.
        settings : dict, optional
            The `settings` will be retrieved or can be provided with keyword argument `settings`.
        """
        settings = settings or self.getSettings()
        channelLoc = channelLoc or self.getChannelLoc(selectedCus, settings)
        changes = {"devices": {}}
        for (mcuId, cuId) in channelLoc.values():
            mcuId, cuId = str(mcuId), str(cuId)
            if not changes['devices'].get(mcuId):
                changes['devices'][mcuId] = {"channels": {}}
            changes['devices'][mcuId]['channels'][cuId] = {'configuration': {name: value}}

        self.setSettings(**changes)

    def setTriggerV(self, value, channelLoc=None, selectedCus=None, settings=None):
        """ Sets the trigger level for the counters for each channel (all selected channels the same value).
        The trigger voltage is in Volts and must be in the range (-10, 10).


        Parameters
        ----------
        value : float
            The trigger level to set (in V) for all channels. Supported range: (-10, 10)V.
        channelLoc : dict, optional
            A dictionary that maps the rank of a cu to the location in terms of [mcuId, cuId]
            for which to perform this action. If not provided, use all of them.
        selectedCus : list of int, optional
            The list of ranks of the detectors (channel units)
            for which to perform this action. If not provided, use all of them.
        settings : dict, optional
            The `settings` will be retrieved or can be provided with keyword argument `settings`.

        Returns
        -------
        None
        """
        if abs(value) > 10:
            raise ValueError('The requested value for Trigger is outside the supported range (-10V, 10V).')

        return self.setChannelConfiguration('triggerV', value, channelLoc=channelLoc, selectedCus=selectedCus, settings=settings)

    def setBiasI(self, value, channelLoc=None, selectedCus=None, settings=None):
        """ Sets the bias current level for each channel (all selected channels the same value).
        The bias current is in Amperes and must be in the range (-83,83)e-6 A.


        Parameters
        ----------
        value : float
            The bias current to set (in A). Supported range: (-83e-6, 83e-6)A.
        channelLoc : dict, optional
            A dictionary that maps the rank of a cu to the location in terms of [mcuId, cuId]
            for which to perform this action. If not provided, use all of them.
        selectedCus : list of int, optional
            The list of ranks of the detectors (channel units)
            for which to perform this action. If not provided, use all of them.
        settings : dict, optional
            The `settings` will be retrieved or can be provided with keyword argument `settings`.

        Returns
        -------
        None

        """
        if abs(value) > 8.3e-6:
            raise ValueError('The value %f A is outside the supported range (-83e-6, 83e-6) A.' % value)

        return self.setChannelConfiguration('biasI', value, channelLoc=channelLoc, selectedCus=selectedCus, settings=settings)

    def setBiasIuA(self, value, channelLoc=None, selectedCus=None, settings=None):
        """ Sets the bias current level for each channel (the same value for all selected channels).
        The bias current is in uA and must be in the range (-83,83) uA.


        Parameters
        ----------
        value : float
            The value of bias current to set (in uA). Supported range: (-83,83)uA.
        channelLoc : dict, optional
            A dictionary that maps the rank of a cu to the location in terms of [mcuId, cuId]
            for which to perform this action. If not provided, use all of them.
        selectedCus : list of int, optional
            The list of ranks of the detectors (channel units)
            for which to perform this action. If not provided, use all of them.
        settings : dict, optional
            The `settings` will be retrieved or can be provided with keyword argument `settings`.

        Returns
        -------
        None

        """
        if abs(value) > 83:
            raise ValueError('The value %f uA is outside the supported range (-83,83) uA' % value)

        return self.setChannelConfiguration('biasI', value * 1e-6, channelLoc=channelLoc,
                                            selectedCus=selectedCus, settings=settings)

    def setBiasIuAMultiple(self, values):
        """ Sets the bias current level for each channel given by the array values.
        The bias current for each channel is in uA and must be in the range (-83,83) uA.


        Parameters
        ----------
        values : array
            Array of floats indicating the bias current to set in each channel (in uA).

        Returns
        -------
        None
        """
        # list of dicts to address all the channels individually.
        rank_map_list = [{key: value} for key, value in self.getRankMap().items()]

        for index, value in enumerate(values):
            # print(f'Current value: {value}. {index+1}/{len(values)}.')
            # check input in range
            if abs(value) > 83:
                raise ValueError('The value %f uA is outside the supported range (-83,83) uA' % value)

            self.setChannelConfiguration('biasI', value * 1e-6, channelLoc=rank_map_list[index], selectedCus=None, settings=None)

    def setTriggerVMultiple(self, values):
        """ Sets the Trigger level for the counter for each channel given by the array values.
        The Trigger current for each channel is in V and must be in the range (-10,10) V.


        Parameters
        ----------
        values : array
            Array of floats indicating the trigger level in each channel (in V).

        Returns
        -------
        None
        """
        # list of dicts to address all the channels individually.
        rank_map_list = [{key: value} for key, value in self.getRankMap().items()]

        for index, value in enumerate(values):
            # print(f'Current value: {value}. {index+1}/{len(values)}.')
            # check input in range
            if abs(value) > 10:
                raise ValueError('The value %f V is outside the supported range (-10,10) V.' % value)

            self.setChannelConfiguration('triggerV', value, channelLoc=rank_map_list[index], selectedCus=None, settings=None)

    def getTriggerV(self, channelLoc=None, selectedCus=None, settings=None):
        """ Gets the trigger level for each channel.

        Parameters
        ----------
        channelLoc : dict, optional
            A dictionary that maps the rank of a cu to the location in terms of [mcuId, cuId]
            for which to perform this action. If not provided, use all of them.
        selectedCus : list of int, optional
            The list of ranks of the detectors (channel units)
            for which to perform this action. If not provided, use all of them.
        settings : dict, optional
            The `settings` will be retrieved or can be provided with keyword argument `settings`.

        Returns
        -------
        list
            a list containing the trigger level for each requested channel

        """
        return self.getChannelConfiguration('triggerV', channelLoc=channelLoc, selectedCus=selectedCus, settings=settings)

    def getBiasI(self, channelLoc=None, selectedCus=None, settings=None):
        """ Gets the bias current for each channel.

        Parameters
        ----------
        channelLoc : dict, optional
            A dictionary that maps the rank of a cu to the location in terms of [mcuId, cuId]
            for which to perform this action. If not provided, use all of them.
        selectedCus : list of int, optional
            The list of ranks of the detectors (channel units)
            for which to perform this action. If not provided, use all of them.
        settings : dict, optional
            The `settings` will be retrieved or can be provided with keyword argument `settings`.

        Returns
        -------
        list
            a list containing the bias current for each requested channel

        """
        return self.getChannelConfiguration('biasI', channelLoc=channelLoc, selectedCus=selectedCus, settings=settings)

    def getBiasIuA(self, channelLoc=None, selectedCus=None, settings=None):
        """ Gets the bias current for each channel in uA.

        Parameters
        ----------
        channelLoc : dict, optional
            A dictionary that maps the rank of a cu to the location in terms of [mcuId, cuId]
            for which to perform this action. If not provided, use all of them.
        selectedCus : list of int, optional
            The list of ranks of the detectors (channel units)
            for which to perform this action. If not provided, use all of them.
        settings : dict, optional
            The `settings` will be retrieved or can be provided with keyword argument `settings`.

        Returns
        -------
        list
            a list containing the bias current in uA for each requested channel

        """
        ans = self.getChannelConfiguration('biasI', channelLoc=channelLoc, selectedCus=selectedCus, settings=settings)
        out = []
        for value in ans:
            out.append(value * 1e6)
        return out

    def stopIV(self):
        return self.jsonrpc("stopIV")

    def rebootSystem(self, **params):
        return self.jsonrpc("rebootSystem", **params)

    def getDevices(self):
        return self.jsonrpc('getDevices')

    def getBackend(self):
        return self.jsonrpc('getBackend')

    def getSettings(self):
        return self.jsonrpc('getSettings')

    def getIvSettings(self):
        return self.jsonrpc('getIvSettings')

    def getIvFile(self, details="", datatype="txt", devicedetails=True):
        """Return a file with the latest iv measurement.

        Parameters
        ----------
        details : str
            Optionally you can pass some extra details/comments in the file.
        datatype : str
            The export datatype, either txt, csv, json.
        devicedetails : bool
            Whether or not to include some extra details of the devices.

        Returns
        -------
        dict
            A dictionary with `ivData` as the root element.
        """
        return self.jsonrpc('getIvFile', details=details, datatype=datatype, devicedetails=devicedetails)

    def getLog(self, lines):
        return self.jsonrpc('getLog', lines=lines)

    def getRankMap(self, settings=None):
        settings = settings or self.getSettings()
        return settings['frontend']['rankMap']

    def getRankByIds(self, mcuId, cuId):
        rankmap = self.getRankMap()
        ranks = [k for k, v in rankmap.items() if v == [mcuId, cuId]]
        if len(ranks) != 1:
            raise KeyError(f"Could not find rank for channel with Ids: {mcuId}.{cuId}!")
        return ranks[0]

    def getAllRanks(self):
        rankmap = self.getRankMap()
        return list(map(lambda x: int(x), rankmap.keys()))

    def getTotalChannels(self):
        return len(self.getRankMap())

    def listChannelIds(self, settings=None):
        return self.RankMap(settings=settings).keys()

    def getCountsHistoryById(self, id, settings=None):
        return self.getChannelInformationById(id=id, kind='data', settings=settings)

    def getAllChannelUnits(self, settings=None):
        """Returns all channel units (cus) as a single list."""
        settings = settings or self.getSettings()
        return [cu for rank, mcu in settings['devices'].items() for cu in mcu['channels']]

    def getIntTime(self, settings=None):
        settings = settings or self.getSettings()
        return settings['backend']['intTime']

    def setIntTime(self, intTime):
        """intTime in (ms) should be in steps of 10ms."""
        return self.setSettings(backend={"intTime": intTime})

    def getTemperatures(self, settings=None, device='1'):
        settings = settings or self.getSettings()
        mcu_data = settings['devices'][device]['data']
        return [mcu_data['temp1'], mcu_data['temp2']]

    def getChannelInformationById(self, id, kind, settings=None):
        """Gets information of the channel at location `id`.

        Parameters
        ----------
        id : int or str
            The `id` of the location as specified by the `rankMap`.
            Always converted to a string because JSON keys are always strings.
        kind : str
            `kind` can be 'configuration', 'data', 'iv', or 'rank'
        settings : dict, optional
            The `settings` will be retrieved or can be provided with keyword argument `settings`.

        Returns
        -------
        dict
            A dictionary with the data of `kind` at that location.
        """
        settings = settings or self.getSettings()
        mcuId, cuId = settings['frontend']['rankMap'][str(id)]
        #print("kind:", settings['devices'][str(mcuId)]['channels'][str(cuId)].keys())
        return settings['devices'][str(mcuId)]['channels'][str(cuId)][kind]

    def getChannelInformationByLoc(self, mcuId, cuId, kind, settings=None):
        """Gets information of the channel at location with `mcuId` and `cuId`.

        Parameters
        ----------
        mcuId : int
            The mcuId of the device.
        cuId : int
            The number of the channel of that deivce.
        kind : str
            `kind` can be 'configuration', 'data', 'iv', or 'rank'
        settings : dict, optional
            The `settings` will be retrieved or can be provided with keyword argument `settings`.

        Returns
        -------
        dict
            A dictionary with the data of `kind` at that location.
        """
        settings = settings or self.getSettings()
        # JSON keys are always strings, even if rankMap tells you otherwise.
        """print(settings.keys())  # JULIA

        for key in settings.keys():
            print(key)
            if key in ['ivTimeStamp', 'total_channels', 'total_microcontrollers']:
                print("  ", settings[key])
            else:
                print("  ", settings[key].keys())"""

        #print(settings['devices'].keys()) # JULIA
        #print(settings['devices'][str(mcuId)].keys()) # JULIA
        #print(settings['devices'][str(mcuId)]['channels'].keys()) # JULIA
        #print(settings['devices'][str(mcuId)]['channels'][str(cuId)].keys()) # JULIA
        #print(settings['devices'][str(mcuId)]['channels'][str(cuId)]['configuration'].keys()) # JULIA
        #print(settings['devices'][str(mcuId)]['channels'][str(cuId)]['rank']) # JULIA
        #input()
        return settings['devices'][str(mcuId)]['channels'][str(cuId)][kind]

    def getChannelLoc(self, selectedCus=None, settings=None):
        """Get the [mcuId, cuId] pairs from the selectedCus, or if not provided, all of them.

        Parameters
        ----------
        settings : dict, optional
            The `settings` will be retrieved or can be provided with keyword argument `settings`.

        Notes
        -----
        Please note that you might get integers back, however, the keys are always strings.

        Returns
        -------
        dict
            A dictionary that maps the rank of a cu to the location in terms of [mcuId, cuId]
        """
        rankMap = self.getRankMap(settings=settings)
        return rankMap if selectedCus is None else dict((i, rankMap[i]) for i in selectedCus)

    def startIv(self, biasIStart, biasIStop, biasIStep, intTime, channelLoc=None, selectedCus=None, settings=None):
        """Start a IV measurement on the cus of `selectedCus` or if not provided all of them.

        Parameters
        ----------
        biasIStart : float
            The current to start (in uA).
        biasIStop : float
            The current to stop (in uA)
        biasIStep : float
            The step size of the sweep (in uA).
        intTime : float
            The integration time (in ms) of a single step.
        selectedCus : list of int, optional
            The list of ranks of the detectors (channel units) for which to perform
            this action. If not provided, use all of them.
        channelLoc: dict, optional
            A dictionary that maps the rank of a cu to the location in terms of [mcuId, cuId]
            for which to perform this action. If not provided, use all of them.
        settings : dict, optional
            The `settings` will be retrieved or can be provided with keyword argument `settings`.

        Returns
        -------
        dict
            The the new updated settings you have send to the server.
        """
        channelLoc = channelLoc or self.getChannelLoc(selectedCus=selectedCus, settings=settings)
        deviceUpdates = [{mcuId: {'channels': {cuId: {'configuration': {
            'rank': rank,
            'biasIStart': biasIStart * 10 ** -6,
            'biasIStop': biasIStop * 10 ** -6,
            'biasIStep': biasIStep * 10 ** -6,
            # The biasSweepT is the amount of cycles a cu (channel unit) runs
            'biasSweepT': intTime / self.cu_inttime,
            'cuStatus': 2,
        }}}}} for rank, (mcuId, cuId) in channelLoc.items()]

        # Reduced specialized merged as mcuId is not unique for each location.
        deviceSettingsUpdated = reduce(merge, deviceUpdates, {})
        return self.setSettings(devices=deviceSettingsUpdated)

    def stopIv(self):
        """Stop the current IV measurement that is running.

        Returns
        -------
        string
            Succes if the IV sweep was stopped succesfully.
        """
        return self.jsonrpc('stopIV')

    def getIvData(self, selectedCus=None, settings=None):
        """Get the IV curves of the last measurement.

        Parameters
        ----------
        selectedCus : list of int, optional
            The list of ranks of the detectors (channel units) for which to perform
            this action. If not provided, use all of them.
        settings : dict, optional
            The `settings` will be retrieved or can be provided with keyword argument `settings`.

        Returns
        -------
        dict:
            A dictionary that maps the location [mcuId, cuId] to a dictionary object
            that contains the `biasI`, `counts`, and `monitorV`.
        """
        settings = settings or self.getSettings()
        channelLoc = self.getChannelLoc(selectedCus=selectedCus, settings=settings)
        traces = {}

        ivDataAll = self.jsonrpc("getIvData")

        for (mcuId, cuId) in channelLoc.values():
            ivData = {}
            rank = self.getRankByIds(mcuId, cuId)
            populated_indices = [i for i, c in enumerate(ivDataAll['counts'][rank]) if c is not None]

            ivData['biasI'] = [ivDataAll['counts']['biasI'][i] for i in populated_indices]
            ivData['counts'] = [ivDataAll['counts'][rank][i] for i in populated_indices]
            ivData['monitorV'] = [ivDataAll['monitorV'][rank][i] for i in populated_indices]

            traces[(mcuId, cuId)] = ivData

        return traces

    def sweepIv(self, biasIStart, biasIStop, biasIStep, intTime, overhead=1, channelLoc=None, selectedCus=None):
        """Start a IV sweep and then return the measured data. Blocks the thread with a time.sleep.

        Parameters
        ----------
        biasIStart : float
            The current to start (in uA).
        biasIStop : float
            The current to stop (in uA)
        biasIStep : float
            The step size of the sweep (in uA).
        intTime : float
            The integration time (in ms) which is the duration of each step.
        overhead : float, default=1
            Wait `overhead` seconds longer than necessary because of latency.
        channelLoc: dict, optional
            A dictionary that maps the rank of a cu to the location in terms of [mcuId, cuId]
            for which to perform this action. If not provided, use all of them.
        selectedCus : list of int, optional
            The list of ranks of the detectors (channel units) for which to perform
            this action. If not provided, use all of them.

        Returns
        -------
        dict
            A dictionary that maps the location [mcuId, cuId] to a dictionary object
            that contains the `biasI`, `counts`, and `monitorV`.
        """
        self.startIv(biasIStart, biasIStop, biasIStep, intTime, channelLoc=channelLoc, selectedCus=selectedCus)
        steps = ((biasIStop - biasIStart) / biasIStep) + 1
        time.sleep((intTime * steps / 1000) + overhead)  # Wait the duration of the sweep time plus a little bit more.
        return self.getIvData(selectedCus=selectedCus, )

    def getIvIntTime(self, settings=None):
        settings = settings or self.getSettings()
        return settings['backend']['ivIntTime']

    def getIvTimeStamp(self, settings=None):
        settings = settings or self.getSettings()
        return settings['backend']['ivTimeStamp']

    def getIvStatus(self):
        return self.jsonrpc('IVStatus')

    def transformToArray(self, data, quantity, channelLoc=None, selectedCus=None, settings=None):
        """Transform your iv data or counts data to a 'a x b' array for `quantity`

        Parameters
        ----------
        data: dict
            Dictionary which is the iv data from getIvData or sweepIv
            or the counts data from getCounts or collectCounts
            Must have been called with asLists=True
        quantity: str
            This is the name of quantity:
            biasI, counts, or monitorV for iv data
            counts, time, monitorV for count data
        channelLoc : dict, optional
            A dictionary that maps the rank of a cu to the location in terms of [mcuId, cuId]
            for which to perform this action. If not provided, use all of them.
        selectedCus : list of int, optional
            The list of ranks of the detectors (channel units)
            for which to perform this action. If not provided, use all of them.
        settings : dict, optional
            The `settings` will be retrieved or can be provided with keyword argument `settings`.

        Returns
        -------
        result: list[list]
            list as 'a x b' data array
            where a is the amount of channels in order of the ranks.
            and b is the amount of data measured.
        """
        channelLoc = channelLoc or self.getChannelLoc(selectedCus, settings)
        res = [[] for _ in channelLoc.keys()]
        for ind, (rank, loc) in enumerate(channelLoc.items()):
            res[ind] = data[tuple(loc)][quantity]
        return res

    def getCounts(self, channelLoc=None, selectedCus=None, settings=None):
        """Get the current counts measurement. The amount of counts during the current integration time.

        Parameters
        ----------
        channelLoc : dict, optional
            A dictionary that maps the rank of a cu to the location in terms of [mcuId, cuId]
            for which to perform this action. If not provided, use all of them.
        selectedCus : list of int, optional
            The list of ranks of the detectors (channel units)
            for which to perform this action. If not provided, use all of them.
        settings : dict, optional
            The `settings` will be retrieved or can be provided with keyword argument `settings`.

        Returns
        -------
        dict
            A dictionary that maps the location [mcuId, cuId] to a dictionary object
            that contains the `counts`, `time`, and `monitorV`.
            The timestamp in the returned data is since the server started.
            The counts are the counts during an integration time period.
        """
        channelLoc = channelLoc or self.getChannelLoc(selectedCus, settings)
        #print(channelLoc)  # JULIA
        return dict(
            ((mcuId, cuId), self.getChannelInformationByLoc(mcuId, cuId, "data"))
            for (mcuId, cuId) in channelLoc.values()
        )

    def collectCounts(self, runtime=10, interval=0.5, asLists=False, channelLoc=None, selectedCus=None):
        """Collect counts every `interval` during the `runtime`. Blocks the thread with a time.sleep.

        Parameters
        ----------
        runtime : float
            The amount of time (in seconds) to collect all the counts.
        interval : float
            Attempt to request the counts every time an interval (in seconds) starts.
        asLists : bool, default=False
            provide `asLists` as True to get the data as lists, instead of dicts.
        channelLoc : dict, optional
            A dictionary that maps the rank of a cu to the location in terms of [mcuId, cuId]
            for which to perform this action. If not provided, use all of them.
        selectedCus : list of int, optional
            The list of ranks of the detectors (channel units)
            for which to perform this action. If not provided, use all of them.
        settings : dict, optional
            The `settings` will be retrieved or can be provided with keyword argument `settings`.

        Returns
        -------
        dict
            A dictionary that maps the location [mcuId, cuId] to a dictionary object
            that contains the `counts`, `time`, and `monitorV`.
            The timestamp in the returned data is since the server started.
            The counts are the counts during an integration time period.

        Notes
        -----
        The result contains `floor(runtime / interval)` points.
        The points are only the points when a new interval starts.
        If a request takes longer than one interval, it just starts a new one when
        the next interval starts.
        Prints a warning to stderr (standard error of console) if points are missed.
        You can increase the interval time to prevent skipped points.
        However the data contains a timestamp, so even with missing points your data is still usefull,
        and it is recommended to rely on the timestamps instead of the interval.
        """
        channelLoc = channelLoc or self.getChannelLoc(selectedCus=selectedCus)
        result = dict(
            (
                (mcuId, cuId),
                {"counts": [], "time": [], "monitorV": []} if asLists else [],
            )
            for (mcuId, cuId) in channelLoc.values()
        )

        #print(result)   # JULIA

        starttime = time.time()
        measured_points = 0
        while time.time() - starttime <= runtime:
            measured_points += 1
            counts = self.getCounts(channelLoc=channelLoc)
            for loc, c in counts.items():
                if not asLists:
                    result[loc].append(c)
                    continue

                for name, value in c.items():
                    result[loc][name].append(value)

            # Wait until you hit the next interval,
            # might skip an interval if the interval is set too short.
            # For missed points a warning is shown.
            time.sleep(interval - ((time.time() - starttime) % interval))

        expected_points = floor(runtime / interval)
        if measured_points != expected_points:
            sys.stderr.write(
                "WARNING: Failed to retrieve all points."
                + " Instead got %i points, expected %i points." % (measured_points, expected_points)
                + " You might want to increase interval,"
                + " but your data is still useful as it contains timestamps.\n",
            )

        #print(result)
        return result

    def getIvHistory(self):
        """
        Gets the IV history for all channels and returns a list of lists with the
        bias current in the first list and the monitor voltage for each CU as the next.

        Returns
        -------
        result: list[list]
            the first list is the bias current
            the n-th list is the monitor voltage for the n-1 CU where n runs from 1 to the number of channels
        """
        data = self.getIvData()

        if len(data) == 0:
            return []
        return [self.transformToArray(data, 'biasI')[0]] + self.transformToArray(data, 'monitorV')

    def getIcHistory(self):
        """
        Gets the IC history for all channels and returns a list of lists with the
        bias current in the first list and the monitor voltage for each CU as the next.

        Returns
        -------
        result: list[list]
            the first list is the bias current
            the n-th list is the counts for the n-1 CU where n runs from 1 to the number of channels
        """
        data = self.getIvData()
        if len(data) == 0:
            return []
        return [self.transformToArray(data, 'biasI')[0]] + self.transformToArray(data, 'counts')


if __name__ == '__main__':
    import os

    websq_domain = os.environ.get("WEBSQ_DOMAIN", 'http://localhost:8080/')
    sq = WebSQController(websq_domain)
