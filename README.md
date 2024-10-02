# ESP32 MicroPython Project

This project is designed to run on an ESP32 microcontroller using MicroPython.

Need to use esptool.py to install micropython firmware compatible with correct ESP32 board version

It integrates a TFT display and an SD card to display images received via Bluetooth Low Energy (BLE).

## Features

- **Display Control**: Display images stored on an SD card on a TFT screen.
- **Bluetooth Connectivity**: Connect and send commands to the ESP32 via BLE.
- **Image Management**: List and display images from the SD card.

## File Structure

```
micropython_project/ 
│
├── main.py                  # Main code for project execution
├── boot.py                  # Initialization code
├── pisca_led.py             # Function to control the LED
├── README.md                # Project description
├── lib/                     # Additional libraries used in the project
│   ├── display.py           # Module for display control
│   └── sd_card.py           # Module for SD card manipulation
└── images/                  # Folder for storing image files
    ├── image1.raw           # Example of a RAW image file
    ├── image2.raw           # Another example of a RAW image file
    └── ...                  # Other image files
```

## Next Steps

1. Implement the `welcome_page()` function to send initial information to the connected device.
2. Improve the `send_notification()` function so that each chunk contains one line of the message, with each new line starting in a new chunk.
3. Implement navigation logic in `send_notification()` for user action options, such as basic commands to advance, go back, confirm (OK), and end.
4. Consider additional improvements for functionality and user experience.
