# sms_module.py - SIM800L GSM Module Handler
import serial
import time
import logging

logger = logging.getLogger('FloodControl.SMS')

class SIM800L:
    def __init__(self, port='/dev/ttyAMA0', baudrate=9600, timeout=1):
        """Initialize SIM800L module"""
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        
    def connect(self):
        """Connect to SIM800L module"""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            time.sleep(2)  # Wait for module to initialize
            logger.info(f"SIM800L connected on {self.port}")
            
            # Test connection
            if self.send_at_command("AT"):
                logger.info("SIM800L module responding")
                
                # Set SMS text mode
                self.send_at_command("AT+CMGF=1")
                
                # Check signal strength
                response = self.send_at_command("AT+CSQ")
                logger.info(f"Signal strength: {response}")
                
                return True
            else:
                logger.error("SIM800L not responding to AT commands")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to SIM800L: {e}")
            return False
    
    def send_at_command(self, command, wait_time=1):
        """Send AT command and get response"""
        try:
            self.ser.write((command + '\r\n').encode())
            time.sleep(wait_time)
            response = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
            return response
        except Exception as e:
            logger.error(f"Error sending AT command '{command}': {e}")
            return None
    
    def send_sms(self, phone_number, message):
        """Send SMS message"""
        try:
            logger.info(f"Sending SMS to {phone_number}: {message[:50]}...")
            
            # Set SMS text mode
            response = self.send_at_command("AT+CMGF=1")
            if "OK" not in response:
                logger.error("Failed to set SMS text mode")
                return False
            
            # Set recipient number
            response = self.send_at_command(f'AT+CMGS="{phone_number}"', wait_time=2)
            
            # Send message content
            self.ser.write(message.encode())
            self.ser.write(bytes([26]))  # Ctrl+Z to send
            
            # Wait for response
            time.sleep(3)
            response = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
            
            if "+CMGS:" in response or "OK" in response:
                logger.info(f"SMS sent successfully to {phone_number}")
                return True
            else:
                logger.error(f"Failed to send SMS. Response: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from SIM800L"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            logger.info("SIM800L disconnected")

# SMS message templates
SMS_MESSAGES = {
    1: "?? YELLOW ALERT: Yawa Bridge flood monitoring detected CAUTION level (90-140mm water). Stay alert and monitor updates.",
    2: "?? ORANGE ALERT: Yawa Bridge is experiencing SERIOUS FLOODING (40-80mm). Avoid the area and prepare for evacuation if necessary.",
    3: "?? RED ALERT: CRITICAL FLOOD LEVEL at Yawa Bridge (0-30mm)! Immediate danger - evacuate now! Emergency services notified."
}
