import asyncio, sys
from onvif import ONVIFCamera
import array
import os
import threading
from six.moves import input
from azure.iot.device import IoTHubDeviceClient, MethodResponse

IP=os.getenv("ONVIF_HOSTNAME")
PORT=80
USER=os.getenv("ONVIF_USERNAME")
PASS=os.getenv("ONVIF_PASSWORD")

STEP_SIZE=0.05
XMAX = STEP_SIZE
XMIN = STEP_SIZE * -1.0
YMAX = STEP_SIZE
YMIN = STEP_SIZE * -1.0
ZXMAX = STEP_SIZE * 2
ZXMIN = STEP_SIZE * 2 * -1.0

continuous_move = None
relative_move = None
home_position = None
absolute_move = None
mycam = ONVIFCamera(IP, PORT, USER, PASS)
media = mycam.create_media_service()
media_profile = media.GetProfiles()[0]
ptz = mycam.create_ptz_service()
active = False
last_command = None

def goto_home_position(ptz, request):
    print('goto_home_position...')
    ptz.GotoHomePosition(request)

def left(ptz, request):
    global active
    if active:
        ptz.Stop({'ProfileToken': request.ProfileToken})
    active = True
    ptz.ContinuousMove(request)

def do_move_relative(ptz, request):
    print('do_move_relative ', request)
    global active
    if active:
        ptz.Stop({'ProfileToken': request.ProfileToken})
    active = True
    ptz.RelativeMove(request)

def do_move_absolute(ptz, request):
    print('do_move_absolute ', request)
    global active
    if active:
        ptz.Stop({'ProfileToken': request.ProfileToken})
    active = True
    ptz.AbsoluteMove(request)

def zoom_in(ptz, request):
    print ('zoom in...')
    print(request)
    request.Translation.PanTilt.x = 0
    request.Translation.PanTilt.y = 0
    request.Translation.Zoom.x = ZXMAX
    #do_move_absolute(ptz, request)
    #request.Position.Zoom.x = ZXMAX
    do_move_relative(ptz, request)

def zoom_out(ptz, request):
    print ('zoom out...')
    print(request)
    request.Translation.PanTilt.x = 0
    request.Translation.PanTilt.y = 0
    request.Translation.Zoom.x = ZXMIN
    #do_move_absolute(ptz, request)
    #request.Position.Zoom.x = ZXMIN
    do_move_relative(ptz, request)

def move_up(ptz, request):
    request.Translation.PanTilt.x = 0
    request.Translation.PanTilt.y = YMAX
    request.Translation.Zoom.x = 0
    do_move_relative(ptz, request)

def move_down(ptz, request):
    request.Translation.PanTilt.x = 0
    request.Translation.PanTilt.y = YMIN
    request.Translation.Zoom.x = 0
    do_move_relative(ptz, request)

# def move_down_relative(ptz, request):
#     print ('move down...')
#     request.Translation.PanTilt.x = 0
#     request.Translation.PanTilt.y = 3
#     do_move_relative(ptz, request)

#def move_up_relative(ptz, request):
#     print ('move up...')
#     request.Translation.PanTilt.x = 0
#     request.Translation.PanTilt.y = 5
#     do_move_relative(ptz, request)

# def move_up_absolute(ptz, request):
#     print ('move up...')
#     request.Position.PanTilt.x = 30.0
#     request.Position.PanTilt.y = 4.0
#     do_move_absolute(ptz, request)

# def move_down_absolute(ptz, request):
#     print ('move down...')
#     request.Position.PanTilt.x = 30.0
#     request.Position.PanTilt.y = 2.0
#     do_move_absolute(ptz, request)

def move_right(ptz, request):
    print ('move right...')
    request.Translation.PanTilt.x = XMAX
    request.Translation.PanTilt.y = 0
    request.Translation.Zoom.x = 0
    do_move_relative(ptz, request)

def move_left(ptz, request):
    print ('move left...')
    request.Translation.PanTilt.x = XMIN
    request.Translation.PanTilt.y = 0
    request.Translation.Zoom.x = 0
    do_move_relative(ptz, request)
    
def move_upleft(ptz, request):
    print ('move up left...')
    request.Translation.PanTilt.x = XMIN
    request.Translation.PanTilt.y = YMAX
    request.Translation.Zoom.x = 0
    do_move_relative(ptz, request)
    
def move_upright(ptz, request):
    print ('move up left...')
    request.Translation.PanTilt.x = XMAX
    request.Translation.PanTilt.y = YMAX
    request.Translation.Zoom.x = 0
    do_move_relative(ptz, request)
    
def move_downleft(ptz, request):
    print ('move down left...')
    request.Translation.PanTilt.x = XMIN
    request.Translation.PanTilt.y = YMIN
    request.Translation.Zoom.x = 0
    do_move_relative(ptz, request)
    
def move_downright(ptz, request):
    print ('move down left...')
    request.Translation.PanTilt.x = XMAX
    request.Translation.PanTilt.y = YMIN
    request.Translation.Zoom.x = 0
    do_move_relative(ptz, request)

def setup_move():    
    global mycam, ptz, media_profile, continuous_move, relative_move, absolute_move, home_position

    # Get PTZ configuration options for getting continuous move range
    request = ptz.create_type('GetConfigurationOptions')
    request.ConfigurationToken = media_profile.PTZConfiguration.token
    ptz_configuration_options = ptz.GetConfigurationOptions(request)

    global continuous_move, relative_move, home_position
    continuous_move = ptz.create_type('ContinuousMove')
    relative_move = ptz.create_type('RelativeMove')
    absolute_move = ptz.create_type('AbsoluteMove')
    home_position = ptz.create_type('GotoHomePosition')

    continuous_move.ProfileToken = media_profile.token
    relative_move.ProfileToken = media_profile.token
    absolute_move.ProfileToken = media_profile.token
    home_position.ProfileToken = media_profile.token

    if continuous_move.Velocity is None:
        continuous_move.Velocity = ptz.GetStatus({'ProfileToken': media_profile.token}).Position

    if relative_move.Translation is None:
        relative_move.Translation = ptz.GetStatus({'ProfileToken': media_profile.token}).Position

    if absolute_move.Position is None:
        absolute_move.Position = ptz.GetStatus({'ProfileToken': media_profile.token}).Position
        #absolute_move.Position.Zoom.space = 'http://www.onvif.org/ver10/tptz/ZoomSpaces/PositionGenericSpace' #ptz_configuration_options.Spaces.AbsoluteZoomPositionSpace[0].URI

    #print(ptz.GetStatus({'ProfileToken': media_profile.token}).Position)
    #print(ptz.GetConfigurations())
    #print(continuous_move)
    print('relative_move: ', relative_move)
    print('absolute_move: ', absolute_move)
    #print(home_position)

    # Get range of pan and tilt
    # NOTE: X and Y are velocity vector
    global XMAX, XMIN, YMAX, YMIN
    #XMAX = ptz_configuration_options.Spaces.RelativePanTiltTranslationSpace[0].XRange.Max
    #XMIN = ptz_configuration_options.Spaces.RelativePanTiltTranslationSpace[0].XRange.Min
    #YMAX = ptz_configuration_options.Spaces.RelativePanTiltTranslationSpace[0].YRange.Max
    #YMIN = ptz_configuration_options.Spaces.RelativePanTiltTranslationSpace[0].YRange.Min
    #ZXMAX = ptz_configuration_options.Spaces.RelativePanTiltTranslationSpace[0].XRange.Max
    #ZXMIN = ptz_configuration_options.Spaces.RelativePanTiltTranslationSpace[0].XRange.Min
    print('ptz_configuration_options.Spaces ', ptz_configuration_options.Spaces)


def readin():
    """Reading from stdin and displaying menu"""
    global last_command

    selection = sys.stdin.readline().strip("\n")
    lov=[ x for x in selection.split(" ") if x != ""]
    
    if len(lov) == 0:
        lov = ['']
        lov[0] = last_command
    
    if lov:
        last_command = lov[0]
        run_command(lov)

    print("")
    print("Your command: ", end='',flush=True)


def run_command(lov):
    global continuous_move, relative_move, home_position, absolute_move, ptz, media_profile, active

    if lov[0].lower() in ["h","ho","home"]:
        goto_home_position(ptz,home_position)

    elif lov[0].lower() in ["l","le","lef","left"]:
        move_right(ptz,relative_move)
    elif lov[0].lower() in ["r","ri","rig","righ","right"]:
        move_left(ptz,relative_move)

    elif lov[0].lower() in ["u","up"]:
        #move_up_absolute(ptz,absolute_move)
        move_up(ptz,relative_move)
    elif lov[0].lower() in ["d","do","dow","down"]:
        #move_down_absolute(ptz,absolute_move)
        move_down(ptz,relative_move)

    elif lov[0].lower() in ["zi","zoom_in"]:
        zoom_in(ptz,relative_move)
    elif lov[0].lower() in ["zo","zoom_out"]:
        zoom_out(ptz,relative_move)

    elif lov[0].lower() in ["ul","up_left"]:
        move_upright(ptz,relative_move)
    elif lov[0].lower() in ["ur","up_right"]:
        move_upleft(ptz,relative_move)
    elif lov[0].lower() in ["dl","down_left"]:
        move_downright(ptz,relative_move)
    elif lov[0].lower() in ["dr","down_right"]:
        move_downleft(ptz,relative_move)

    elif lov[0].lower() in ["s","st","sto","stop"]:
        ptz.Stop({'ProfileToken': relative_move.ProfileToken})
        active = False
    else:
        print("What are you asking?\tI only know, 'zi (zoom in)','zo (zoom out)','up','down','left','right', 'ul' (up left), \n\t\t\t'ur' (up right), 'dl' (down left), 'dr' (down right) and 'stop'")

    print(ptz.GetStatus({'ProfileToken': media_profile.token}).Position)

def message_handler(message):
    command = message.data.decode("utf-8")
    print("the data in the message received was ")
    print(command)

    lov = ['']
    lov[0] = command
    run_command(lov)

    #print("custom properties are")
    #print(message.custom_properties)

# Define behavior for handling methods
def method_request_handler(method_request):
    # Determine how to respond to the method request based on the method name
    print(method_request.name)
    print(method_request.payload)
    if method_request.name in ['zoom_in', 'zoom_out']:
        payload = {"result": True, "data": "OK"}  # set response payload
        status = 200  # set return status code
        lov = ['']
        lov[0] = method_request.name
        run_command(lov)
        print("executed {}".format(method_request.name))
    elif method_request.name == "move":
        payload = {"result": True, "data": "OK"}  # set response payload
        status = 200  # set return status code
        run_command(method_request.payload)
        print("executed move {}".format(method_request.payload))
    elif method_request.name == "stream":
        payload = {"result": True, "data": "OK"}  # set response payload
        status = 200  # set return status code
        print("executed right")
    else:
        payload = {"result": False, "data": "unknown method"}  # set response payload
        status = 200  # set return status code
        print("executed unknown method: " + method_request.name)

    # Send the response
    method_response = MethodResponse.create_from_method_request(method_request, status, payload)
    device_client.send_method_response(method_response)

            
if __name__ == '__main__':
    conn_str = os.getenv("IOTHUB_DEVICE_CONNECTION_STRING")
    device_client = IoTHubDeviceClient.create_from_connection_string(conn_str, websockets=True)
    device_client.on_message_received = message_handler
    device_client.on_method_request_received = method_request_handler
    device_client.connect()

    setup_move()
    #goto_home_position(ptz,home_position)

    loop = asyncio.get_event_loop()
    try:
        loop.add_reader(sys.stdin,readin)
        print("Use Ctrl-C to quit")
        print("Your command: ", end='',flush=True)
        loop.run_forever()
    except:
        pass
    finally:
        loop.remove_reader(sys.stdin)
        loop.close()
        device_client.shutdown()


