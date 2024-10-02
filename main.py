# Import libraries
import machine
from machine import Pin, SPI, PWM
from lib.sdcard import SDCard
import os
import time
from lib.ili9341 import Display, color565
import bluetooth
from micropython import const
from time import sleep

# Pin definitions for the displays; customize according to the display model
TFT_CS = const(15)
TFT_DC = const(2)
TFT_SCK = const(14)
TFT_MOSI = const(13)
TFT_PWM = const(27)

# Pin definitions for the SD card SPI; customize according to the schematic
SD_CS = const(5)
SD_SCK = const(18)
SD_MOSI = const(23)
SD_MISO = const(19)

# Turn off the red LED
RLED = const(4)
RLED_pin = Pin(RLED, Pin.OUT)
RLED_pin.value(1)

# Initialize the SPI for the TFT display
def init_display():
    spi = SPI(2, baudrate=20000000, sck=Pin(TFT_SCK), mosi=Pin(TFT_MOSI))
    display = Display(spi, cs=Pin(TFT_CS), dc=Pin(TFT_DC), rst=Pin(0))
    pwm = PWM(Pin(TFT_PWM), freq=1000)
    pwm.duty(1023)  # Turn on the backlight
    return display

# Initialize the SPI for the SD card
def init_sd():
    try:
        spi2 = SPI(1, baudrate=20000000, sck=Pin(SD_SCK), mosi=Pin(SD_MOSI), miso=Pin(SD_MISO))
        sd = SDCard(spi2, Pin(SD_CS))
        vfs = os.VfsFat(sd)
        os.mount(vfs, "/sd")
        return vfs
    except Exception as e:
        print("Error initializing SD card:", e)
        return None

# Initialize Bluetooth
def init_bluetooth(device_name):
    ble = bluetooth.BLE()
    ble.active(True)
    ble.config(gap_name=device_name)
    return ble

# BLE advertising
def advertise_ble(ble, device_name):
    adv_data = bytearray([
        0x02, 0x01, 0x06,  # Flags
        0x03, 0x03, 0x0D, 0x18,  # Complete List of 16-bit Service Class UUIDs
        len(device_name) + 1, 0x09  # Length of local name field + type of local name
    ]) + device_name.encode('utf-8')

    ble.gap_advertise(100, adv_data)

# Setup BLE services and characteristics
def setup_ble_services(ble):
    SERVICE_UUID = bluetooth.UUID(0x180A)
    CHARACTERISTIC_UUID = bluetooth.UUID(0x2A00)
    characteristics = (
        (CHARACTERISTIC_UUID, bluetooth.FLAG_READ | bluetooth.FLAG_WRITE | bluetooth.FLAG_NOTIFY),
    )
    service = (
        (SERVICE_UUID, characteristics),
    )
    srv = ble.gatts_register_services(service)
    return srv[0]

# Function to display an image from the SD card on the display
def display_image(display, image_path):
    try:
        prepare_display(display)
        display.draw_image(image_path)
        return True
    except OSError as e:
        print("Error opening file:", e)
        return False

def prepare_display(display, brightness=None, clear=True, bg_color=color565(0, 0, 0)):
    """Prepare the display for use.
    Args:
        display: Display object to be manipulated.
        brightness (Optional int): Brightness level (0-255).
        clear (Optional bool): Whether to clear the display (default True).
        bg_color (Optional int): Background color when clearing the display (default black).
    """
    display.clear()

    if brightness is not None:
        display.set_brightness(brightness)  # Adjust brightness if necessary

    if clear:
        display.clear(bg_color)  # Clear the display with the chosen background color

# Function to list images on the SD card
def list_images():
    try:
        return [f for f in os.listdir('/sd') if f.endswith('.jpg') or f.endswith('.raw')]
    except OSError as e:
        print("Error listing files:", e)
        return []

def send_notification(ble, char_handle, message, chunk_size=20):
    """
    Function to send a message as a notification via BLE, splitting into chunks if necessary.
    
    :param ble: BLE object to send notifications.
    :param char_handle: BLE characteristic handle to send the data.
    :param message: The message to be sent as a notification.
    :param chunk_size: Maximum size of each chunk (default 20 bytes).
    """
    data = message.encode('utf-8')
    
    # Split the data into smaller chunks and send
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        ble.gatts_notify(0, char_handle, chunk)

# Callback for handling write events on the BLE characteristic
def on_command_received(event, ble, display, char_handle):
    print(f"Value written: ", ble.gatts_read(event[1]))
    try:
        # Read the value sent by the BLE client
        value = ble.gatts_read(event[1])
        command = value.decode('utf-8')
        
        # Check if the command starts with 'DI:' to display an image
        if command.startswith('DI:'):
            image_name = command.split(':')[1]
            image_path = f'/sd/{image_name}'
            if display_image(display, image_path):
                print(f"Image {image_name} displayed on the display.")
                message = "OK: Image displayed"
                send_notification(ble, char_handle, message)
            else:
                message = "ERROR: Failed to display image"
                send_notification(ble, char_handle, message)

        # Check if the command is 'R' or 'r' to display the red screen
        elif command in ['R', 'r']:
            prepare_display(display)
            display.fill_rectangle(0, 0, 229, 309, color565(255, 0, 0))
            print(f"Red screen displayed")
            message = "red screen"
            send_notification(ble, char_handle, message)

        # Check if the command is 'G' or 'g' to display the green screen
        elif command in ['G', 'g']:
            prepare_display(display)
            display.fill_rectangle(0, 0, 229, 309, color565(0, 255, 0))
            print(f"Green screen displayed")
            message = "green screen"
            send_notification(ble, char_handle, message)

        # Check if the command is 'B' or 'b' to display the blue screen
        elif command in ['B', 'b']:
            prepare_display(display)
            display.fill_rectangle(0, 0, 229, 309, color565(0, 0, 255))
            print(f"Blue screen displayed")
            message = "blue screen"
            send_notification(ble, char_handle, message)
        
        # Check if the command is 'W' or 'w' to display the white screen
        elif command in ['W', 'w']:
            prepare_display(display)
            display.fill_rectangle(0, 0, 229, 309, color565(255, 255, 255))
            print(f"White screen displayed")
            message = "white screen"
            send_notification(ble, char_handle, message)
        
        # Check if the command is 'BK' or 'bk' to display the black screen
        elif command in ['BK', 'bk']:
            prepare_display(display)
            display.fill_rectangle(0, 0, 229, 309, color565(0, 0, 0))
            print(f"Black screen displayed")
            message = "black screen"
            send_notification(ble, char_handle, message)

        # Check if the command is 'LI' to list images
        elif command == 'LI':
            images = list_images()
            images_str = ','.join(images)
            message = images_str
            send_notification(ble, char_handle, message)
            
    except Exception as e:
        print("Error processing command:", e)
        message = "ERROR: Failed to process command"
        send_notification(ble, char_handle, message)

# BLE interrupt handler
def ble_irq(event, data, ble, display, char_handle):
    global is_connected
    if event == const(3):  # Write event
        on_command_received(data, ble, display, char_handle)
    elif event == const(1):
        is_connected = True
        print("Client connected via BLE!")
    elif event == const(2):
        is_connected = False
        print("Client disconnected from BLE.")
        advertise_ble(ble, "ESP32_Test")

# Main initialization
def main():
    global is_connected
    is_connected = False
    
    # Initialize components
    display = init_display()
    init_sd()
    device_name = "ESP32_Test"
    ble = init_bluetooth(device_name)

    # Setup BLE service
    char_handles = setup_ble_services(ble)
    char_handle = char_handles[0]

    # Start advertising
    advertise_ble(ble, device_name)
    print("BLE active and service registered.")

    # Set BLE callback
    ble.irq(handler=lambda event, data: ble_irq(event, data, ble, display, char_handle))

    while True:
        if is_connected:
            sleep(1)  # Adjust as necessary; add your code here for when the device is connected
        else:
            sleep(0.1)  # Polling delay when not connected

# Run the main function
if __name__ == '__main__':
    main()
