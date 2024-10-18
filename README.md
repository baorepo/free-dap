# Free-DAP

This is a free and open implementation of the CMSIS-DAP debugger firmware.

Both SWD and JTAG protocols are supported. However JTAG was not well tested due to lack of
good targets. If you have any issues with it - let me know and I'll try to help.

## Platform requirements

To create a CMSIS-DAP compliant debugger, your platform must:
 * Implement USB HID (and raw bulk for CMSIS-DAP v2) device able to receive and send arbitrary payloads
 * Provide configuration file dap_config.h with definitions for hardware-dependent calls
 * Call dap_init() at the initialization time
 * Call dap_process_request() for every received request and send the response back

## CMSIS-DAP version support

Free-DAP library itself is protocol agnostic and implementation of the specific version
of the CMSIS-DAP protocol (v1 or v2) is up to the individual platforms.

Currently RP2040, SAM D11 and SAM D21 implementaitons were updated to support CMSIS-DAP v2.
Other platforms would be updated if requested or needed by me.

## Configuration

For complete list of settings see one of the existing configuration file, they are
pretty obvious.

To configure clock frequency you need to specify two parameters:
  * DAP_CONFIG_DELAY_CONSTANT - clock timing constant. This constant can be determined
    by calling dap_clock_test() with varying parameter value and measuring the frequency
    on the SWCLK pin. Delay constant value is the value of the parameter at which
    output frequency equals to 1 kHz.
  * DAP_CONFIG_FAST_CLOCK - threshold for switching to fast clock routines. This value
    defines the frequency, at which more optimal pin manipulation functions are used.
    This is the frequency produced by dap_clock_test(1) on the SWCLK pin.
    You can also measure maximum achievable frequency on your platform by calling dap_clock_test(0).

Your configuration file will need to define the following pin manipulation functions:

 * DAP_CONFIG_SWCLK_TCK_write()
 * DAP_CONFIG_SWDIO_TMS_write()
 * DAP_CONFIG_TDO_write()
 * DAP_CONFIG_nTRST_write()
 * DAP_CONFIG_nRESET_write()
 * DAP_CONFIG_SWCLK_TCK_read()
 * DAP_CONFIG_SWDIO_TMS_read()
 * DAP_CONFIG_TDI_read()
 * DAP_CONFIG_TDO_read()
 * DAP_CONFIG_nTRST_read()
 * DAP_CONFIG_nRESET_read()
 * DAP_CONFIG_SWCLK_TCK_set()
 * DAP_CONFIG_SWCLK_TCK_clr()
 * DAP_CONFIG_SWDIO_TMS_in()
 * DAP_CONFIG_SWDIO_TMS_out()

Note that all pin manipulation functions are required even if one of the interfaces (JTAG or SWD) is not enabled.

Additionally configuration file must provide basic initialization and control functions:

 * DAP_CONFIG_SETUP()
 * DAP_CONFIG_DISCONNECT()
 * DAP_CONFIG_CONNECT_SWD()
 * DAP_CONFIG_CONNECT_JTAG()
 * DAP_CONFIG_LED()
 * DAP_CONFIG_DELAY()

## Tools

A complete RP2040 build requres bin2uf2 utility to generate UF2 file suitable for the RP2040 MSC bootloader.
This utility can be downloded [here](https://github.com/ataradov/tools/tree/master/bin2uf2).

## Binaries

Generally there are no pre-built binaries due to effort required to maintain
them and low potential benefit because of custom hardware requirement.

For RP2040 and Raspberry Pi Pico board specifically there is a binary, since
it is a standard and a widely available board that has a nonvolatile bootloader.

The UF2 file is located [here](bin/free_dap_rp2040.uf2). Simply boot into
a BootROM MSC mode and copy that file to the drive.

I will try to do my best to keep this binary in sync with the code updates, but
it is a manual process, so I may forget. Let me know if you have any issues.

The pins used are as follows:

| GPIO | Function |
|:---:|:---|
| 11 | SWCLK/TCK |
| 12 | SWDIO/TMS |
| 13 | TDI |
| 14 | TDO |
| 15 | nRESET |
| 0 | VCP TX |
| 1 | VCP RX |
| 2 | VCP Status |
| 25 (LED) | DAP Status |






要更改这段代码以便适配新的 USB 设备名称和 PID/VID，您需要修改以下几个变量：

idVendor 和 idProduct： 这些值用于标识您的 USB 设备。您可以更改以下部分：

c
复制代码
.idVendor           = 0x6666,  // 修改为新的 Vendor ID
.idProduct          = 0x9902,   // 修改为新的 Product ID
字符串描述符： 如果您希望更改设备的名称和其他字符串描述符（如制造商和序列号），可以在 usb_strings 数组中找到并更改：

c
复制代码
[USB_STR_MANUFACTURER]  = "Alex Taradov",  // 修改为您的制造商名称
[USB_STR_PRODUCT]       = "Combined VCP and CMSIS-DAP Adapter", // 修改为您的产品名称
[USB_STR_SERIAL_NUMBER] = usb_serial_number,  // 可选，修改序列号
USB 设备描述符： 如果需要，您还可以更改以下描述符的内容，以符合新设备的要求：

c
复制代码
.bcdDevice          = 0x0100,  // 修改为新的设备版本
配置相关的参数（如果需要）： 如果您的设备使用了不同的 USB 配置或接口，您可能需要调整 usb_configuration_hierarchy 中的接口和描述符数量等参数。