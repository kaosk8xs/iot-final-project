#include "LoRaWan_APP.h"
#include <Arduino.h>

uint8_t devEui[] = {0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08};
bool overTheAirActivation = true;
uint8_t appEui[] = {0x01, 0xAB, 0x02, 0xCD, 0x03, 0xEF, 0x04, 0x05};  // you should set whatever your TTN generates. TTN calls this the joinEUI, they are the same thing. 
uint8_t appKey[] = {0x3C, 0x1F, 0x76, 0x00, 0x50, 0xF6, 0x41, 0x24, 0xBD, 0xBA, 0x61, 0x2B, 0xA7, 0x45, 0x1C, 0x38};  // you should set whatever your TTN generates 

//These are only used for ABP, for OTAA, these values are generated on the Nwk Server, you should not have to change these values
uint8_t nwkSKey[] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
uint8_t appSKey[] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
uint32_t devAddr =  (uint32_t)0x00000000;  

/*LoraWan channelsmask*/
uint16_t userChannelsMask[6]={ 0xFF00,0x0000,0x0000,0x0000,0x0000,0x0000 };

/*LoraWan region, select in arduino IDE tools*/
LoRaMacRegion_t loraWanRegion = ACTIVE_REGION;  // we define this as a user flag in the .ini file. 

/*LoraWan Class, Class A and Class C are supported*/
DeviceClass_t  loraWanClass = CLASS_A;

/*the application data transmission duty cycle.  value in [ms].*/
uint32_t appTxDutyCycle = 20 * 1000;

/*ADR enable*/
bool loraWanAdr = true;

// uint32_t license[4] = {};

/* Indicates if the node is sending confirmed or unconfirmed messages */
bool isTxConfirmed = true;

/* Application port */
uint8_t appPort = 1;
/*!
* Number of trials to transmit the frame, if the LoRaMAC layer did not
* receive an acknowledgment. The MAC performs a datarate adaptation,
* according to the LoRaWAN Specification V1.0.2, chapter 18.4, according
* to the following table:
*
* Transmission nb | Data Rate
* ----------------|-----------
* 1 (first)       | DR
* 2               | DR
* 3               | max(DR-1,0)
* 4               | max(DR-1,0)
* 5               | max(DR-2,0)
* 6               | max(DR-2,0)
* 7               | max(DR-3,0)
* 8               | max(DR-3,0)
*
* Note, that if NbTrials is set to 1 or 2, the MAC will not decrease
* the datarate, in case the LoRaMAC layer did not receive an acknowledgment
*/
uint8_t confirmedNbTrials = 8;

/* Prepares the payload of the frame */
static void prepareTxFrame( uint8_t port )
{
	/*appData size is LORAWAN_APP_DATA_MAX_SIZE which is defined in "commissioning.h".
	*appDataSize max value is LORAWAN_APP_DATA_MAX_SIZE.
	*if enabled AT, don't modify LORAWAN_APP_DATA_MAX_SIZE, it may cause system hanging or failure.
	*if disabled AT, LORAWAN_APP_DATA_MAX_SIZE can be modified, the max value is reference to lorawan region and SF.
	*for example, if use REGION_CN470, 
	*the max value for different DR can be found in MaxPayloadOfDatarateCN470 refer to DataratesCN470 and BandwidthsCN470 in "RegionCN470.h".
	*/
    // This data can be changed, just make sure to change the datasize as well. 
	// read temperature from internal temperature sensor
	// float temperature = randr(0,10000);
	// temperature = temperature / 100.0;
	float temperature = temperatureRead();
	printf("Temperature: %f\n", temperature);
	appDataSize = 5;
	appData[0] = 0x0e;
	for (int i = 0; i < 4; i++)
	{
		appData[i+1] = *((uint8_t *)&temperature + i);
	}
	for (int i = 0; i < appDataSize; i++) {
		printf("%02X ", appData[i]);
	}
}

RTC_DATA_ATTR bool firstrun = true;

void setup() {
	Serial.begin(115200);
  Mcu.begin();
  if(firstrun)
  {
    LoRaWAN.displayMcuInit();
    firstrun = false;
  }
	deviceState = DEVICE_STATE_INIT;
}

void loop()
{
	switch( deviceState )
	{
		case DEVICE_STATE_INIT:
		{
#if(LORAWAN_DEVEUI_AUTO)
			LoRaWAN.generateDeveuiByChipID();
#endif
			LoRaWAN.init(loraWanClass,loraWanRegion);
			break;
		}
		case DEVICE_STATE_JOIN:
		{
      LoRaWAN.displayJoining();
			LoRaWAN.join();
			if (deviceState == DEVICE_STATE_SEND){
			 	LoRaWAN.displayJoined();
			}
			break;
		}
		case DEVICE_STATE_SEND:
		{
      		LoRaWAN.displaySending();
			prepareTxFrame( appPort );
			LoRaWAN.send();
			deviceState = DEVICE_STATE_CYCLE;
			break;
		}
		case DEVICE_STATE_CYCLE:
		{
			// Schedule next packet transmission
			txDutyCycleTime = appTxDutyCycle; // + randr( 0, APP_TX_DUTYCYCLE_RND );
			LoRaWAN.cycle(txDutyCycleTime);
			deviceState = DEVICE_STATE_SLEEP;
			break;
		}
		case DEVICE_STATE_SLEEP:
		{
      		LoRaWAN.displayAck();
			LoRaWAN.sleep(loraWanClass);
			break;
		}
		default:
		{
			deviceState = DEVICE_STATE_INIT;
			break;
		}
	}
}