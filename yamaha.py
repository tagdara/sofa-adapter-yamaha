#!/usr/bin/python3

import sys, os
# Add relative paths for the directory where the adapter is located as well as the parent
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__),'../../base'))

from sofabase import sofabase
from sofabase import adapterbase
import devices



import math
import random
from collections import namedtuple
import json
import definitions
import asyncio
import aiohttp
import struct
import xml.etree.ElementTree as et
from collections import defaultdict
import socket


class BroadcastProtocol:

    def __init__(self, loop, log, keyphrases=[], returnmessage=None):
        try:
            self.log=log
            self.loop = loop
            self.keyphrases=keyphrases
            self.returnMessage=returnmessage
        except:
            self.log.error('Error initializing SSDP')


    def connection_made(self, transport):
        try:
            self.transport = transport
            sock = transport.get_extra_info("socket")
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.log.info('.. ssdp now listening: %s' % sock)
        except:
            self.log.error('Error initializing SSDP on connection made')


    def datagram_received(self, data, addr):
        try:
            data=data.decode()
            for phrase in self.keyphrases:
                if data.find(phrase)>-1 and data.find("<?xml")>-1:
                    event=self.etree_to_dict(et.fromstring(data[data.find("<?xml"):]))
                    self.log.info('-> ssdp %s' % event)
                    self.processUPNPevent(event)
                    #return str(data)
        except:
            self.log.error('Error during datagram_received')


    def broadcast(self, data):
        try:
            self.log.info('>> ssdp/broadcast %s' % data)
            self.transport.sendto(data.encode(), ('192.168.0.255', 9000))
        except:
            self.log.error('Error during broadcast')

    def etree_to_dict(self, t):
        
        try:
            d = {t.tag: {} if t.attrib else None}
            children = list(t)
            if children:
                dd = defaultdict(list)
                for dc in map(self.etree_to_dict, children):
                    for k, v in dc.items():
                        dd[k].append(v)
                d = {t.tag: {k: v[0] if len(v) == 1 else v for k, v in dd.items()}}
            if t.attrib:
                d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())
            if t.text:
                text = t.text.strip()
                if children or t.attrib:
                    if text:
                        d[t.tag]['#text'] = text
                else:
                    d[t.tag] = text
            return d
        except:
            self.log.error('Error converting etree to dict')


    def processUPNPevent(self, event):   

        try:
            #self.log.info('Event: %s' % event)
            asyncio.ensure_future(self.returnMessage(event))

        except:
            self.log.info("Error processing UPNP Event: %s " % upnpxml,exc_info=True)


class yamahaXML():

    def __init__(self, log=None, dataset=None):
        self.log=log
        self.dataset=dataset
        self.definitions=definitions.yamahaDefinitions

    def etree_to_dict(self, t):
        
        d = {t.tag: {} if t.attrib else None}
        children = list(t)
        if children:
            dd = defaultdict(list)
            for dc in map(self.etree_to_dict, children):
                for k, v in dc.items():
                    dd[k].append(v)
            d = {t.tag: {k: v[0] if len(v) == 1 else v for k, v in dd.items()}}
        if t.attrib:
            d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())
        if t.text:
            text = t.text.strip()
            if children or t.attrib:
                if text:
                    d[t.tag]['#text'] = text
            else:
                d[t.tag] = text
        return d


    def data2xml(self, d, name='YAMAHA_AV'):
        r = et.Element(name)
        r.set('cmd','PUT')
        return et.tostring(self.buildxml(r, d))

    def buildxml(self, r, d):
        if isinstance(d, dict):
            for k, v in d.items():
                s = et.SubElement(r, k)
                self.buildxml(s, v)
        elif isinstance(d, tuple) or isinstance(d, list):
            for v in d:
                s = et.SubElement(r, 'i')
                self.buildxml(s, v)
        elif isinstance(d, str):
            r.text = d
        else:
            r.text = str(d)
        return r

        
    async def sendCommand(self, command_data):
        try:
            data=self.data2xml(command_data).decode()
            socket.setdefaulttimeout(1)

            url = 'http://%s:%s/YamahaRemoteControl/ctrl' % (self.dataset.config['address'], self.dataset.config['port'])
            #self.log.info('Command: %s %s' % (url, data))
            headers = { "Content-type": "text/xml" }
            self.log.info('Sending: %s %s %s' % (url, data, headers))
            async with aiohttp.ClientSession() as client:
                response=await client.post(url, data=data, headers=headers)
                xml=await response.read()
                self.log.debug('XML resp: %s' % xml)
                if xml:
                    ydata=self.etree_to_dict(et.fromstring(xml))
                    return ydata['YAMAHA_AV']
                else:
                    return {}
        except:
            self.log.error("send_command error",exc_info=True)
    
    async def getState(self, itemState):
        try:
            url = 'http://%s:%s/YamahaRemoteControl/ctrl' % (self.dataset.config['address'], self.dataset.config['port'])
            headers = { "Content-type": "text/xml" }
            data=self.definitions.itemStates[itemState]
            async with aiohttp.ClientSession() as client:
                response=await client.post(url, data=data, headers=headers)
                xml=await response.read()
                if xml:
                    ydata=self.etree_to_dict(et.fromstring(xml))
                    return ydata['YAMAHA_AV']
                else:
                    return {}

        except:
            self.log.error('Error sending command', exc_info=True)
    
    async def main(self):
        async with aiohttp.ClientSession() as client:
            html = await self.authenticate(client)
            return html


class yamaha(sofabase):

    class EndpointHealth(devices.EndpointHealth):

        @property            
        def connectivity(self):
            return 'OK'

    class PowerController(devices.PowerController):

        @property            
        def powerState(self):
            return "ON" if self.nativeObject['Basic_Status']['Power_Control']['Power']=="On" else "OFF"

        async def TurnOn(self, correlationToken=''):
            try:
                return await self.adapter.setAndUpdate(self.device, {"System": {"Power_Control": {"Power": "On"}}}, correlationToken)
            except:
                self.adapter.log.error('!! Error during TurnOn', exc_info=True)
                return None
        
        async def TurnOff(self, correlationToken=''):
            try:
                return await self.adapter.setAndUpdate(self.device, {"System": {"Power_Control": {"Power": "Standby"}}}, correlationToken)
            except:
                self.adapter.log.error('!! Error during TurnOff', exc_info=True)
                return None

    class InputController(devices.InputController):

        @property            
        def input(self):
            try:
                # Yamaha returns the name of the input instead of it's id, but the name can be overridden on the device and it will still
                # reply with the original value. For example, an input_sel of "AV4" would typically represent AV_4, even if AV_4's name was
                # changed to "TV".  
                # In order to deal with their cheese, stripping the underscore from the id and comparing with the input_sel will almost always work
                # to get the right id.
                
                # look for it properly
                
                if self.nativeObject['Basic_Status']['Input']['Input_Sel'] in self.adapter.dataset.nativeDevices['Receiver']['System']['Config']['Name']['Input']:
                    return self.dataset.nativeDevices['Receiver']['System']['Config']['Name']['Input'][self.nativeObject['Basic_Status']['Input']['Input_Sel']]
                
                # if that doesn't work, walk the list, find the right answer and return the user name
                for inp in self.adapter.dataset.nativeDevices['Receiver']['System']['Config']['Name']['Input']:
                    if inp.replace('_','')==self.nativeObject['Basic_Status']['Input']['Input_Sel']:
                        return self.adapter.dataset.nativeDevices['Receiver']['System']['Config']['Name']['Input'][inp]
                
                # if nothing else just return the raw value and hope for the best
                return self.nativeObject['Basic_Status']['Input']['Input_Sel']
            except:
                self.adapter.log.error('Error checking input status', exc_info=True)
                return ""
                    
        async def SelectInput(self, payload, correlationToken=''):
            try:
                for inp in self.adapter.dataset.nativeDevices['Receiver']['System']['Config']['Name']['Input']:
                    if self.adapter.dataset.nativeDevices['Receiver']['System']['Config']['Name']['Input'][inp]==payload['input']:
                        return await self.adapter.setAndUpdate(self.device, {"Main_Zone": {"Input": {"Input_Sel":  inp.replace('_','')}}}, correlationToken)
                        
                return None
            except:
                self.log.error('!! Error during SelectInput', exc_info=True)
                return None

    class InputLockModeController(devices.ModeController):

        @property            
        def mode(self):
            try:
                #self.log.info('NativeObject: %s' % self.nativeObject)
                for mode in self._supportedModes:
                    if 'managed' in self.nativeObject and self.nativeObject["managed"]["input_lock"]==self._supportedModes[mode]:
                        return "%s.%s" % (self.name, mode)
            except:
                self.log.error('!! error getting input lock mode', exc_info=True)
                return ""

        async def SetMode(self, payload, correlationToken=''):
            try:
                if payload['mode'].split('.')[1] in self._supportedModes:
                    newmode=self._supportedModes[payload['mode'].split('.')[1]] # Yamaha modes have spaces, so set based on display name
                    if newmode=="Locked":
                        locked_input=self.nativeObject['Basic_Status']['Input']['Input_Sel']
                    else:
                        locked_input=""
                    x=await self.adapter.setAndUpdate(self.device, {"managed": {'input_lock':newmode, "locked_input":locked_input}}, correlationToken)
                    return x
                self.log.error('!! error - did not find mode %s' % payload)
            except:
                self.adapter.log.error('Error setting mode status %s' % payload, exc_info=True)
            return {}

    class SurroundModeController(devices.ModeController):

        @property            
        def mode(self):
            try:
                if self.nativeObject['Basic_Status']['Surround']['Program_Sel']['Current']['Straight']=="On":
                    return "%s.Straight" % self.name
                for mode in self._supportedModes:
                    if self.nativeObject['Basic_Status']['Surround']['Program_Sel']['Current']['Sound_Program']==self._supportedModes[mode]:
                        return "%s.%s" % (self.name, mode)
            except:
                self.log.error('!! error getting surround mode', exc_info=True)
                return ""

        async def SetMode(self, payload, correlationToken=''):
            try:
                if payload['mode'].split('.')[1] in self._supportedModes:
                    newmode=self._supportedModes[payload['mode'].split('.')[1]] # Yamaha modes have spaces, so set based on display name
                    if newmode=="Straight":
                        return await self.adapter.setAndUpdate(self.device, {"Main_Zone": {"Surround": {"Program_Sel": { "Current": {"Straight": "On" }}}}}, correlationToken)
                    else:
                        await self.adapter.setAndUpdate(self.device, {"Main_Zone": {"Surround": {"Program_Sel": { "Current": {"Straight": "Off" }}}}}, correlationToken, update=False)
                        return await self.adapter.setAndUpdate(self.device, {"Main_Zone": {"Surround": {"Program_Sel": { "Current": {"Sound_Program": newmode }}}}}, correlationToken)
                self.log.error('!! error - did not find mode %s' % payload)
            except:
                self.adapter.log.error('Error setting mode status %s' % payload, exc_info=True)
            return {}

    class DecoderModeController(devices.ModeController):

        @property            
        def mode(self):
            try:
                for mode in self._supportedModes:
                    if self.nativeObject['Input']['Decoder_Sel']['Current']==self._supportedModes[mode]:
                        return "%s.%s" % (self.name, mode)
            except:
                self.log.error('!! error getting surround mode', exc_info=True)
                return ""

        async def SetMode(self, payload, correlationToken=''):
            try:
                if payload['mode'].split('.')[1] in self._supportedModes:
                    newmode=self._supportedModes[payload['mode'].split('.')[1]] # Yamaha modes have spaces, so set based on display name
                    # need to find right command to set mode but this is stubbed out for the moment
                    #return await self.adapter.setAndUpdate(self.device, {"Main_Zone": {"Surround": {"Program_Sel": { "Current": {"Sound_Program": newmode }}}}}, correlationToken)
                self.log.error('!! error - did not find mode %s' % payload)
            except:
                self.adapter.log.error('Error setting mode status %s' % payload, exc_info=True)
            return {}

    class SpeakerController(devices.SpeakerController):

        @property            
        def volume(self):
            try:
                #volrange={'max':15, 'min':-70}
                volrange={'max':0, 'min':-80}
                zvolume=float(self.nativeObject['Basic_Status']['Volume']['Lvl']['Val'])/10
                zpos=int(round(((volrange['max']-volrange['min'])-(volrange['max']-zvolume))*(100/(volrange['max']-volrange['min']))))
                return zpos
            except:
                self.log.error('!! Error during volume', exc_info=True)

        @property            
        def mute(self):
            return self.nativeObject['Basic_Status']['Volume']['Mute']!='Off'

        async def SetVolume(self, payload, correlationToken=''):
            try:
                volrange={'max':0, 'min':-80}
                unitconv=(volrange['max']-volrange['min'])/100
                realvol=str(int(float(unitconv* int(payload['volume'])))+volrange['min'])+"0"
                return await self.adapter.setAndUpdate(self.device, {"Main_Zone": {"Volume": {"Lvl": { "Val": realvol, "Exp": 1, "Unit": "dB"}}}}  , correlationToken)
            except:
                self.log.error('!! Error during SetVolume', exc_info=True)
                self.adapter.connect_needed=True
                return None

        async def SetMute(self, payload, correlationToken=''):
            try:
                self.log.warn('!! SetMute has not been implemented yet.')
            except:
                self.log.error('!! Error during SetMute', exc_info=True)
                self.adapter.connect_needed=True
                return None


    class adapterProcess():


        def __init__(self, log=None, dataset=None, notify=None, request=None, loop=None, **kwargs):

            self.definitions=definitions.yamahaDefinitions
            self.dataset=dataset
            self.ssdpkeywords=self.dataset.config['ssdpkeywords']
            self.log=log
            self.notify=notify
            if not loop:
                self.loop = asyncio.new_event_loop()
            else:
                self.loop=loop


        async def check_lock(self):

            try:
                if self.dataset.nativeDevices['Receiver']['Main_Zone']["managed"]["input_lock"]=="Locked":
                    if self.dataset.nativeDevices['Receiver']['Main_Zone']["managed"]["locked_input"]!=self.dataset.nativeDevices['Receiver']['System']['Config']['Name']['Input']:
                        self.log.info('Setting input back to locked value: %s' % self.dataset.nativeDevices['Receiver']['Main_Zone']["managed"]["locked_input"])
                        command= {"Main_Zone": {"Input": {"Input_Sel":  self.dataset.nativeDevices['Receiver']['Main_Zone']["managed"]["locked_input"].replace('_','')}}}
                        await self.receiver.sendCommand(command)
            except:
                self.log.error('Error updating state of receiver InputLock: %s' % (itemState), exc_info=True)


        async def updateInputState(self, itemState):

            try:
                result=await self.receiver.getState(itemState)
                for item in result:
                    if item.find('@')!=0:
                        await self.dataset.ingest({ "Receiver": {item: result[item]} })
            except:
                self.log.error('Error updating state of receiver: %s' % (itemState), exc_info=True)

        async def updateInputLockState(self, managed_data):

            try:
                await self.dataset.ingest({ "Receiver": {"Main_Zone": { "managed" : dict(managed_data) }}})
            except:
                self.log.error('Error updating state of receiver InputLock: %s' % (managed_data), exc_info=True)

            
        async def updateState(self, itemState):

            try:
                result=await self.receiver.getState(itemState)
                for item in result:
                    if item.find('@')!=0:
                        await self.dataset.ingest({ "Receiver": {item: result[item]} })
            except:
                self.log.error('Error updating state of receiver: %s' % (itemState), exc_info=True)


        async def processUPNP(self, message):
            try:
                message=message['YAMAHA_AV']
                # Some messages might not be power or volume, but this works for now
                await self.updateState('basic_status')
                await self.check_lock()

            except:
                self.log.error('Error processing UPNP: %s' % message, exc_info=True)


        async def updateEverything(self):
            
            try:
                for detail in self.definitions.systemStates:
                    await self.updateState(detail)
                # zone state
                for detail in self.definitions.mainZoneStates:
                    await self.updateState(detail)
            
            except:
                self.log.error('Error updating everything', exc_info=True)

        def make_ssdp_sock(self):
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', 1900))
            group = socket.inet_aton('239.255.255.250')
            mreq = struct.pack('4sL', group, socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)    
            return sock            
            
        async def start(self):

            try:
                self.address=self.dataset.config['address']
                self.port=self.dataset.config['port']
                self.receiver=yamahaXML(log=self.log, dataset=self.dataset)
                await self.updateEverything()
                await self.updateInputLockState({"input_lock": "Unlocked", "locked_input": ""})
                self.inputlist=[]
            except:
                self.log.error('error with update',exc_info=True)

            try:
                sock=self.make_ssdp_sock()
                self.ssdp = self.loop.create_datagram_endpoint(lambda: BroadcastProtocol(self.loop, self.log, self.ssdpkeywords, returnmessage=self.processUPNP), sock=sock)
                await self.ssdp
            except:
                self.log.error('error with ssdp',exc_info=True)


        async def addSmartDevice(self, path):
            
            try:
                if path.split("/")[2]=="Main_Zone":
                    return self.addSmartSpeaker(path.split("/")[2], "Receiver")

            except:
                self.log.error('Error defining smart device', exc_info=True)
                return False


        def getInputList(self):
            
            try:
                inputlist=[]
                rawinp=self.dataset.nativeDevices['Receiver']['System']['Config']['Name']['Input']
                for inp in rawinp:
                    if rawinp[inp] in self.dataset.config['inputs']:
                        inputlist.append(self.dataset.nativeDevices['Receiver']['System']['Config']['Name']['Input'][inp])
                return inputlist
            except:
                self.log.error('Error getting input list', exc_info=True)
                return []
                    
        def getSurroundList(self):
            
            # This data does not seem to be available for retrieval from the device, but it is documented in the API with the following options
            # which may or may not be present on any given device.
            # Configure which ones are visible in the config file.
            
            surroundmodes=["Hall in Munich", "Hall in Vienna", "Hall in Amsterdam", "Church in Freiburg", "Church in Royaumont", "Chamber", 
                            "Village Vanguard", "Warehouse Loft","Cellar Club","The Roxy Theatre","The Bottom Line","Sports","Action Game", 
                            "Roleplaying Game", "Music Video", "Recital/Opera", "Standard","Spectacle","Sci-Fi","Adventure","Drama","Mono Movie",
                            "2ch Stereo","7ch Stereo","9ch Stereo","Straight Enhancer","7ch Enhancer","Surround Decoder"]
            
            try:
                surroundlist=[]
                for surround in surroundmodes:
                    if 'surrounds' not in self.dataset.config or surround in self.dataset.config['surrounds']:
                        surroundlist.append(surround)
                return surroundlist
            except:
                self.log.error('Error getting input list', exc_info=True)
                return []

            

        def addSmartSpeaker(self, deviceid, name="Receiver"):
            
            nativeObject=self.dataset.nativeDevices['Receiver'][deviceid]
            if name not in self.dataset.devices:
                if "Input" in nativeObject:
                    device=devices.alexaDevice('yamaha/Receiver/%s' % deviceid, name, displayCategories=["RECEIVER"], adapter=self)
                    device.InputController=yamaha.InputController(device=device, inputs=self.getInputList())
                    device.PowerController=yamaha.PowerController(device=device)
                    device.EndpointHealth=yamaha.EndpointHealth(device=device)
                    modes={}
                    for mode in self.dataset.config['surrounds']:
                        modes[mode.replace(" ", "")]=mode
                    device.SurroundModeController=yamaha.SurroundModeController('Surround', device=device, supportedModes=modes)
                    device.InputLockModeController=yamaha.InputLockModeController('InputLock', device=device, 
                            supportedModes={'Unlocked': 'Unlocked', "Locked": "Locked"})

                    #device.SurroundController=yamaha.SurroundController(device=device, inputs=self.getSurroundList())
                    device.SpeakerController=yamaha.SpeakerController(device=device)
                    return self.dataset.newaddDevice(device)
            return False

        def getNativeFromEndpointId(self, endpointId):
            
            try:
                return endpointId.split(":")[2]
            except:
                return False

        async def setAndUpdate(self, device, command, correlationToken='', update=True):
            
            #  General Set and Update process for insteon. Most direct commands should just set the native command parameters
            #  and then call this to apply the change
            
            try:
                if 'managed' in command:
                    if 'input_lock' in command['managed']:
                        await self.updateInputLockState(command['managed'])
                else:
                    response=await self.receiver.sendCommand(command)
                    self.log.info('<- %s' % response)
                if update:
                    await self.updateEverything()
                    return await self.dataset.generateResponse(device.endpointId, correlationToken)
            except:
                self.log.error('!! Error during Set and Update: %s %s / %s %s' % (deviceid, command, controllerprop, controllervalue), exc_info=True)
            return None
                
        async def virtualList(self, itempath, query={}):

            try:
                if itempath=="inputs":
                    return self.dataset.nativeDevices['Receiver']['System']['Config']['Name']['Input']
                return {}

            except:
                self.log.error('Error getting virtual controller types for %s' % itempath, exc_info=True)


if __name__ == '__main__':
    adapter=yamaha(name="yamaha")
    adapter.start()