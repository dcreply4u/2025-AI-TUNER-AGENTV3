"""
Complete ISO 14229 UDS Implementation
All 26 UDS services according to ISO 14229 standard.
"""

from __future__ import annotations

import struct
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Tuple, Dict, Any, Callable

LOGGER = logging.getLogger(__name__)


class UDSService(Enum):
    """UDS Service IDs (ISO 14229)."""
    # Diagnostic and Communication Management
    DIAGNOSTIC_SESSION_CONTROL = 0x10
    ECU_RESET = 0x11
    CLEAR_DIAGNOSTIC_INFORMATION = 0x14
    READ_DTC_INFORMATION = 0x19
    READ_DATA_BY_IDENTIFIER = 0x22
    READ_MEMORY_BY_ADDRESS = 0x23
    READ_SCALING_DATA_BY_IDENTIFIER = 0x24
    SECURITY_ACCESS = 0x27
    COMMUNICATION_CONTROL = 0x28
    AUTHENTICATION = 0x29
    READ_DATA_BY_PERIODIC_IDENTIFIER = 0x2A
    DYNAMICALLY_DEFINE_DATA_IDENTIFIER = 0x2C
    WRITE_DATA_BY_IDENTIFIER = 0x2E
    WRITE_MEMORY_BY_ADDRESS = 0x3D
    TESTER_PRESENT = 0x3E
    SECURE_DATA_TRANSMISSION = 0x84
    CONTROL_DTC_SETTING = 0x85
    RESPONSE_ON_EVENT = 0x86
    LINK_CONTROL = 0x87
    
    # Data Transmission
    READ_DATA_BY_IDENTIFIER_POSITIVE = 0x62  # Positive response
    WRITE_DATA_BY_IDENTIFIER_POSITIVE = 0x6E  # Positive response
    
    # Stored Data Transmission
    REQUEST_DOWNLOAD = 0x34
    REQUEST_UPLOAD = 0x35
    TRANSFER_DATA = 0x36
    REQUEST_TRANSFER_EXIT = 0x37
    REQUEST_FILE_TRANSFER = 0x38
    
    # Input/Output Control
    ROUTINE_CONTROL = 0x31
    INPUT_OUTPUT_CONTROL_BY_IDENTIFIER = 0x2F


class NegativeResponseCode(Enum):
    """UDS Negative Response Codes (ISO 14229)."""
    GENERAL_REJECT = 0x10
    SERVICE_NOT_SUPPORTED = 0x11
    SUB_FUNCTION_NOT_SUPPORTED = 0x12
    INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT = 0x13
    RESPONSE_TOO_LONG = 0x14
    BUSY_REPEAT_REQUEST = 0x21
    CONDITIONS_NOT_CORRECT = 0x22
    REQUEST_SEQUENCE_ERROR = 0x24
    NO_RESPONSE_FROM_SUBNET_COMPONENT = 0x25
    FAILURE_PREVENTS_EXECUTION_OF_REQUESTED_ACTION = 0x26
    REQUEST_OUT_OF_RANGE = 0x31
    SECURITY_ACCESS_DENIED = 0x33
    INVALID_KEY = 0x35
    EXCEED_NUMBER_OF_ATTEMPTS = 0x36
    REQUIRED_TIME_DELAY_NOT_EXPIRED = 0x37
    UPLOAD_DOWNLOAD_NOT_ACCEPTED = 0x70
    TRANSFER_DATA_SUSPENDED = 0x71
    GENERAL_PROGRAMMING_FAILURE = 0x72
    WRONG_BLOCK_SEQUENCE_COUNTER = 0x73
    REQUEST_CORRECTLY_RECEIVED_RESPONSE_PENDING = 0x78
    SUB_FUNCTION_NOT_SUPPORTED_IN_ACTIVE_SESSION = 0x7E
    SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION = 0x7F


@dataclass
class UDSResponse:
    """UDS response structure."""
    service_id: int
    data: bytes
    is_positive: bool
    negative_response_code: Optional[NegativeResponseCode] = None
    timestamp: float = 0.0


class CompleteUDSServices:
    """Complete ISO 14229 UDS services implementation."""
    
    def __init__(self, can_interface):
        """
        Initialize UDS services.
        
        Args:
            can_interface: CAN interface for communication
        """
        self.can = can_interface
        self.timeout = 2.0
        self.p2_timeout = 50.0  # P2 timeout (ms)
        self.p2_star_timeout = 5000.0  # P2* timeout (ms)
        self.current_session = 0x01  # Default session
        self.security_level = 0x00  # No security access
        self.tester_present_active = False
        self.tester_present_interval = 2.0
        self.last_tester_present = 0.0
        
        LOGGER.info("Complete UDS services initialized")
    
    def send_request(
        self,
        service_id: int,
        data: bytes = b'',
        timeout: Optional[float] = None,
    ) -> Optional[UDSResponse]:
        """
        Send UDS request and receive response.
        
        Args:
            service_id: UDS service ID
            data: Service data
            timeout: Request timeout (default: self.timeout)
        
        Returns:
            UDSResponse or None if timeout/error
        """
        timeout = timeout or self.timeout
        payload = bytes([service_id]) + data
        
        try:
            self.can.send(payload)
            response_data = self.can.recv(timeout=timeout)
            
            if not response_data or len(response_data) < 1:
                return None
            
            response_service = response_data[0]
            
            # Check for positive response
            if response_service == (service_id + 0x40):
                return UDSResponse(
                    service_id=service_id,
                    data=response_data[1:],
                    is_positive=True,
                    timestamp=time.time(),
                )
            
            # Check for negative response
            elif response_service == 0x7F:
                if len(response_data) >= 3:
                    nrc = NegativeResponseCode(response_data[2])
                    return UDSResponse(
                        service_id=service_id,
                        data=response_data[3:],
                        is_positive=False,
                        negative_response_code=nrc,
                        timestamp=time.time(),
                    )
            
            return None
            
        except Exception as e:
            LOGGER.error("Error sending UDS request: %s", e)
            return None
    
    # ========================================================================
    # Diagnostic and Communication Management (0x10-0x3E, 0x84-0x87)
    # ========================================================================
    
    def diagnostic_session_control(
        self,
        session_type: int = 0x01,
    ) -> Optional[UDSResponse]:
        """
        Service 0x10: Diagnostic Session Control.
        
        Args:
            session_type: 0x01=default, 0x02=programming, 0x03=extended,
                         0x04=safetySystem, 0x40-0x5F=OEM specific
        
        Returns:
            UDSResponse with session parameters
        """
        response = self.send_request(UDSService.DIAGNOSTIC_SESSION_CONTROL.value, bytes([session_type]))
        if response and response.is_positive:
            self.current_session = session_type
        return response
    
    def ecu_reset(self, reset_type: int = 0x01) -> Optional[UDSResponse]:
        """
        Service 0x11: ECU Reset.
        
        Args:
            reset_type: 0x01=hardReset, 0x02=keyOffOnReset, 0x03=softReset,
                       0x04=enableRapidPowerShutDown, 0x05=disableRapidPowerShutDown
        
        Returns:
            UDSResponse
        """
        return self.send_request(UDSService.ECU_RESET.value, bytes([reset_type]))
    
    def clear_diagnostic_information(
        self,
        group_of_dtc: bytes = b'\xFF\xFF\xFF',
    ) -> Optional[UDSResponse]:
        """
        Service 0x14: Clear Diagnostic Information.
        
        Args:
            group_of_dtc: 3-byte DTC group mask (0xFF 0xFF 0xFF = all DTCs)
        
        Returns:
            UDSResponse
        """
        return self.send_request(UDSService.CLEAR_DIAGNOSTIC_INFORMATION.value, group_of_dtc)
    
    def read_dtc_information(
        self,
        report_type: int = 0x01,
        dtc_status_mask: Optional[int] = None,
        dtc_and_status_record: Optional[bytes] = None,
    ) -> Optional[UDSResponse]:
        """
        Service 0x19: Read DTC Information.
        
        Args:
            report_type: 0x01=numberOfDTCByStatusMask, 0x02=DTCByStatusMask,
                        0x03=DTCSnapshotIdentification, 0x04=DTCSnapshotRecordByDTCNumber,
                        0x05=DTCStoredDataByRecordNumber, 0x06=DTCStoredDataByRecordNumber,
                        0x07=numberOfDTCBySeverityMaskRecord, 0x08=DTCBySeverityMaskRecord,
                        0x09=severityInformationOfDTC, 0x0A=supportedDTC, 0x0B=firstTestFailedDTC,
                        0x0C=firstConfirmedDTC, 0x0D=mostRecentTestFailedDTC,
                        0x0E=mostRecentConfirmedDTC, 0x0F=DTCFaultDetectionCounter,
                        0x10=DTCwithPermanentStatus
            dtc_status_mask: Status mask (for report_type 0x01, 0x02)
            dtc_and_status_record: DTC and status record (for report_type 0x04)
        
        Returns:
            UDSResponse with DTC information
        """
        data = bytes([report_type])
        
        if dtc_status_mask is not None:
            data += bytes([dtc_status_mask])
        
        if dtc_and_status_record:
            data += dtc_and_status_record
        
        return self.send_request(UDSService.READ_DTC_INFORMATION.value, data)
    
    def read_data_by_identifier(
        self,
        data_identifier: int,
    ) -> Optional[UDSResponse]:
        """
        Service 0x22: Read Data By Identifier.
        
        Args:
            data_identifier: 2-byte DID (Data Identifier)
        
        Returns:
            UDSResponse with data
        """
        did_bytes = struct.pack(">H", data_identifier)
        return self.send_request(UDSService.READ_DATA_BY_IDENTIFIER.value, did_bytes)
    
    def read_memory_by_address(
        self,
        address: int,
        address_format: int = 0x00,
        memory_size: int = 0,
        memory_size_format: int = 0x00,
    ) -> Optional[UDSResponse]:
        """
        Service 0x23: Read Memory By Address.
        
        Args:
            address: Memory address
            address_format: Address length (0x00-0x0F)
            memory_size: Number of bytes to read
            memory_size_format: Size length (0x00-0x0F)
        
        Returns:
            UDSResponse with memory data
        """
        # Format: [addressFormat] [address] [memorySizeFormat] [memorySize]
        address_bytes = address.to_bytes(address_format + 1, byteorder='big')
        size_bytes = memory_size.to_bytes(memory_size_format + 1, byteorder='big')
        data = bytes([address_format]) + address_bytes + bytes([memory_size_format]) + size_bytes
        return self.send_request(UDSService.READ_MEMORY_BY_ADDRESS.value, data)
    
    def read_scaling_data_by_identifier(
        self,
        data_identifier: int,
    ) -> Optional[UDSResponse]:
        """
        Service 0x24: Read Scaling Data By Identifier.
        
        Args:
            data_identifier: 2-byte DID
        
        Returns:
            UDSResponse with scaling data
        """
        did_bytes = struct.pack(">H", data_identifier)
        return self.send_request(UDSService.READ_SCALING_DATA_BY_IDENTIFIER.value, did_bytes)
    
    def security_access(
        self,
        security_level: int,
        key: Optional[bytes] = None,
        seed_key_func: Optional[Callable[[bytes], bytes]] = None,
    ) -> Optional[UDSResponse]:
        """
        Service 0x27: Security Access.
        
        Args:
            security_level: 0x01-0x41 (odd = requestSeed), 0x02-0x42 (even = sendKey)
            key: Pre-calculated key (if available)
            seed_key_func: Function to calculate key from seed
        
        Returns:
            UDSResponse
        """
        # Request seed (odd level)
        if security_level % 2 == 1:
            response = self.send_request(UDSService.SECURITY_ACCESS.value, bytes([security_level]))
            
            if response and response.is_positive and len(response.data) > 0:
                seed = response.data
                
                # Calculate key
                if seed_key_func:
                    calculated_key = seed_key_func(seed)
                elif key:
                    calculated_key = key
                else:
                    LOGGER.warning("No key calculation method provided")
                    return response
                
                # Send key (even level)
                key_level = security_level + 1
                return self.send_request(UDSService.SECURITY_ACCESS.value, bytes([key_level]) + calculated_key)
            
            return response
        
        # Send key directly (even level)
        if key:
            return self.send_request(UDSService.SECURITY_ACCESS.value, bytes([security_level]) + key)
        
        LOGGER.error("Key required for even security level")
        return None
    
    def communication_control(
        self,
        control_type: int,
        communication_type: int = 0x01,
    ) -> Optional[UDSResponse]:
        """
        Service 0x28: Communication Control.
        
        Args:
            control_type: 0x00=enableRxAndTx, 0x01=enableRxAndDisableTx,
                         0x02=disableRxAndEnableTx, 0x03=disableRxAndDisableTx
            communication_type: 0x01=normalCommunicationMessages, 0x02=networkManagementCommunicationMessages,
                               0x03=networkManagementCommunicationMessagesWithSpecificAddress
        
        Returns:
            UDSResponse
        """
        data = bytes([control_type, communication_type])
        return self.send_request(UDSService.COMMUNICATION_CONTROL.value, data)
    
    def authentication(
        self,
        authentication_type: int,
        authentication_data: Optional[bytes] = None,
    ) -> Optional[UDSResponse]:
        """
        Service 0x29: Authentication.
        
        Args:
            authentication_type: Authentication method
            authentication_data: Authentication data
        
        Returns:
            UDSResponse
        """
        data = bytes([authentication_type])
        if authentication_data:
            data += authentication_data
        return self.send_request(UDSService.AUTHENTICATION.value, data)
    
    def read_data_by_periodic_identifier(
        self,
        transmission_mode: int,
        periodic_data_identifier: int,
    ) -> Optional[UDSResponse]:
        """
        Service 0x2A: Read Data By Periodic Identifier.
        
        Args:
            transmission_mode: 0x00=stopSending, 0x01-0xFE=sendEveryXms, 0xFF=sendOnChange
            periodic_data_identifier: 2-byte PID
        
        Returns:
            UDSResponse
        """
        pid_bytes = struct.pack(">H", periodic_data_identifier)
        data = bytes([transmission_mode]) + pid_bytes
        return self.send_request(UDSService.READ_DATA_BY_PERIODIC_IDENTIFIER.value, data)
    
    def dynamically_define_data_identifier(
        self,
        definition_type: int,
        did: int,
        source_dids: List[int],
        positions: Optional[List[int]] = None,
        memory_address: Optional[int] = None,
        memory_size: Optional[int] = None,
    ) -> Optional[UDSResponse]:
        """
        Service 0x2C: Dynamically Define Data Identifier.
        
        Args:
            definition_type: 0x01=defineByIdentifier, 0x02=defineByMemoryAddress,
                            0x03=clearDynamicallyDefinedDID
            did: Target DID (2 bytes)
            source_dids: List of source DIDs
            positions: Byte positions (for definition_type 0x01)
            memory_address: Memory address (for definition_type 0x02)
            memory_size: Memory size (for definition_type 0x02)
        
        Returns:
            UDSResponse
        """
        did_bytes = struct.pack(">H", did)
        data = bytes([definition_type]) + did_bytes
        
        if definition_type == 0x01:  # Define by identifier
            for i, source_did in enumerate(source_dids):
                source_did_bytes = struct.pack(">H", source_did)
                position = positions[i] if positions else 0
                data += source_did_bytes + bytes([position])
        
        elif definition_type == 0x02:  # Define by memory address
            if memory_address and memory_size:
                addr_bytes = struct.pack(">I", memory_address)
                size_bytes = struct.pack(">I", memory_size)
                data += addr_bytes + size_bytes
        
        # definition_type 0x03 (clear) needs no additional data
        
        return self.send_request(UDSService.DYNAMICALLY_DEFINE_DATA_IDENTIFIER.value, data)
    
    def write_data_by_identifier(
        self,
        data_identifier: int,
        data: bytes,
    ) -> Optional[UDSResponse]:
        """
        Service 0x2E: Write Data By Identifier.
        
        Args:
            data_identifier: 2-byte DID
            data: Data to write
        
        Returns:
            UDSResponse
        """
        did_bytes = struct.pack(">H", data_identifier)
        return self.send_request(UDSService.WRITE_DATA_BY_IDENTIFIER.value, did_bytes + data)
    
    def input_output_control_by_identifier(
        self,
        data_identifier: int,
        control_option_record: bytes,
        control_enable_mask: Optional[bytes] = None,
    ) -> Optional[UDSResponse]:
        """
        Service 0x2F: Input Output Control By Identifier.
        
        Args:
            data_identifier: 2-byte DID
            control_option_record: Control data
            control_enable_mask: Enable mask
        
        Returns:
            UDSResponse
        """
        did_bytes = struct.pack(">H", data_identifier)
        data = did_bytes + control_option_record
        if control_enable_mask:
            data += control_enable_mask
        return self.send_request(UDSService.INPUT_OUTPUT_CONTROL_BY_IDENTIFIER.value, data)
    
    def routine_control(
        self,
        routine_identifier: int,
        control_type: int,
        routine_option_record: Optional[bytes] = None,
    ) -> Optional[UDSResponse]:
        """
        Service 0x31: Routine Control.
        
        Args:
            routine_identifier: 2-byte routine ID
            control_type: 0x01=start, 0x02=stop, 0x03=requestResults
            routine_option_record: Optional routine parameters
        
        Returns:
            UDSResponse
        """
        rid_bytes = struct.pack(">H", routine_identifier)
        data = rid_bytes + bytes([control_type])
        if routine_option_record:
            data += routine_option_record
        return self.send_request(UDSService.ROUTINE_CONTROL.value, data)
    
    def request_download(
        self,
        memory_address: int,
        memory_size: int,
        address_and_length_format: int = 0x44,  # 4 bytes address, 4 bytes size
        data_format: int = 0x00,
    ) -> Optional[UDSResponse]:
        """
        Service 0x34: Request Download.
        
        Args:
            memory_address: Target memory address
            memory_size: Number of bytes to download
            address_and_length_format: Format byte (high nibble=address length, low nibble=size length)
            data_format: Data format identifier
        
        Returns:
            UDSResponse with maxNumberOfBlockLength
        """
        addr_length = (address_and_length_format >> 4) & 0x0F
        size_length = address_and_length_format & 0x0F
        
        addr_bytes = memory_address.to_bytes(addr_length + 1, byteorder='big')
        size_bytes = memory_size.to_bytes(size_length + 1, byteorder='big')
        
        data = bytes([address_and_length_format, data_format]) + addr_bytes + size_bytes
        return self.send_request(UDSService.REQUEST_DOWNLOAD.value, data)
    
    def request_upload(
        self,
        memory_address: int,
        memory_size: int,
        address_and_length_format: int = 0x44,
        data_format: int = 0x00,
    ) -> Optional[UDSResponse]:
        """
        Service 0x35: Request Upload.
        
        Args:
            memory_address: Source memory address
            memory_size: Number of bytes to upload
            address_and_length_format: Format byte
            data_format: Data format identifier
        
        Returns:
            UDSResponse with maxNumberOfBlockLength
        """
        addr_length = (address_and_length_format >> 4) & 0x0F
        size_length = address_and_length_format & 0x0F
        
        addr_bytes = memory_address.to_bytes(addr_length + 1, byteorder='big')
        size_bytes = memory_size.to_bytes(size_length + 1, byteorder='big')
        
        data = bytes([address_and_length_format, data_format]) + addr_bytes + size_bytes
        return self.send_request(UDSService.REQUEST_UPLOAD.value, data)
    
    def transfer_data(
        self,
        block_sequence_number: int,
        data: bytes,
    ) -> Optional[UDSResponse]:
        """
        Service 0x36: Transfer Data.
        
        Args:
            block_sequence_number: Block sequence (0x00-0xFF, wraps around)
            data: Data block
        
        Returns:
            UDSResponse
        """
        return self.send_request(
            UDSService.TRANSFER_DATA.value,
            bytes([block_sequence_number]) + data
        )
    
    def request_transfer_exit(self) -> Optional[UDSResponse]:
        """
        Service 0x37: Request Transfer Exit.
        
        Returns:
            UDSResponse
        """
        return self.send_request(UDSService.REQUEST_TRANSFER_EXIT.value)
    
    def request_file_transfer(
        self,
        file_path_and_name_length: int,
        file_path_and_name: bytes,
        file_size_parameter: Optional[int] = None,
    ) -> Optional[UDSResponse]:
        """
        Service 0x38: Request File Transfer.
        
        Args:
            file_path_and_name_length: Length of file path/name
            file_path_and_name: File path/name
            file_size_parameter: Optional file size
        
        Returns:
            UDSResponse
        """
        data = bytes([file_path_and_name_length]) + file_path_and_name
        if file_size_parameter is not None:
            data += struct.pack(">I", file_size_parameter)
        return self.send_request(UDSService.REQUEST_FILE_TRANSFER.value, data)
    
    def write_memory_by_address(
        self,
        address: int,
        address_format: int = 0x00,
        memory_size: int = 0,
        memory_size_format: int = 0x00,
        data: bytes = b'',
    ) -> Optional[UDSResponse]:
        """
        Service 0x3D: Write Memory By Address.
        
        Args:
            address: Memory address
            address_format: Address length
            memory_size: Number of bytes to write
            memory_size_format: Size length
            data: Data to write
        
        Returns:
            UDSResponse
        """
        address_bytes = address.to_bytes(address_format + 1, byteorder='big')
        size_bytes = memory_size.to_bytes(memory_size_format + 1, byteorder='big')
        payload = bytes([address_format]) + address_bytes + bytes([memory_size_format]) + size_bytes + data
        return self.send_request(UDSService.WRITE_MEMORY_BY_ADDRESS.value, payload)
    
    def tester_present(
        self,
        sub_function: int = 0x00,
    ) -> Optional[UDSResponse]:
        """
        Service 0x3E: Tester Present.
        
        Args:
            sub_function: 0x00=sendResponse, 0x80=suppressPositiveResponse
        
        Returns:
            UDSResponse
        """
        response = self.send_request(UDSService.TESTER_PRESENT.value, bytes([sub_function]))
        self.last_tester_present = time.time()
        return response
    
    def start_tester_present(self, interval: float = 2.0) -> None:
        """Start periodic tester present messages."""
        self.tester_present_active = True
        self.tester_present_interval = interval
        LOGGER.info("Tester present started (interval: %.1fs)", interval)
    
    def stop_tester_present(self) -> None:
        """Stop periodic tester present messages."""
        self.tester_present_active = False
        LOGGER.info("Tester present stopped")
    
    def secure_data_transmission(
        self,
        security_data_request_record: bytes,
    ) -> Optional[UDSResponse]:
        """
        Service 0x84: Secure Data Transmission.
        
        Args:
            security_data_request_record: Security data
        
        Returns:
            UDSResponse with security data response
        """
        return self.send_request(UDSService.SECURE_DATA_TRANSMISSION.value, security_data_request_record)
    
    def control_dtc_setting(
        self,
        dtc_setting_type: int,
        dtc_setting_control_option_record: Optional[bytes] = None,
    ) -> Optional[UDSResponse]:
        """
        Service 0x85: Control DTC Setting.
        
        Args:
            dtc_setting_type: 0x01=on, 0x02=off
            dtc_setting_control_option_record: Optional control data
        
        Returns:
            UDSResponse
        """
        data = bytes([dtc_setting_type])
        if dtc_setting_control_option_record:
            data += dtc_setting_control_option_record
        return self.send_request(UDSService.CONTROL_DTC_SETTING.value, data)
    
    def response_on_event(
        self,
        event_type: int,
        event_window_time: int,
        event_type_record: Optional[bytes] = None,
    ) -> Optional[UDSResponse]:
        """
        Service 0x86: Response On Event.
        
        Args:
            event_type: 0x00=stopResponseOnEvent, 0x01-0xFE=eventType, 0xFF=clearAll
            event_window_time: Time window in seconds
            event_type_record: Optional event parameters
        
        Returns:
            UDSResponse
        """
        data = bytes([event_type]) + struct.pack(">H", event_window_time)
        if event_type_record:
            data += event_type_record
        return self.send_request(UDSService.RESPONSE_ON_EVENT.value, data)
    
    def link_control(
        self,
        link_control_type: int,
        link_control_option_record: Optional[bytes] = None,
    ) -> Optional[UDSResponse]:
        """
        Service 0x87: Link Control.
        
        Args:
            link_control_type: 0x01=verifyBaudrateTransitionWithFixedBaudrate,
                               0x02=verifyBaudrateTransitionWithSpecificBaudrate,
                               0x03=transitionBaudrate
            link_control_option_record: Optional control data
        
        Returns:
            UDSResponse
        """
        data = bytes([link_control_type])
        if link_control_option_record:
            data += link_control_option_record
        return self.send_request(UDSService.LINK_CONTROL.value, data)
    
    def get_supported_services(self) -> List[int]:
        """Get list of supported UDS services (would be determined by ECU)."""
        # This would typically be determined by querying the ECU
        # For now, return all implemented services
        return [service.value for service in UDSService if service.value < 0x80]


__all__ = [
    "CompleteUDSServices",
    "UDSService",
    "NegativeResponseCode",
    "UDSResponse",
]

