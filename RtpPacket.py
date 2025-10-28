# RtpPacket.py (chỉ phần thay thế encode)
from time import time
HEADER_SIZE = 12

class RtpPacket:
    header = bytearray(HEADER_SIZE)

    def __init__(self):
        pass

    def encode(self, version, padding, extension, cc, seqnum, marker, pt, ssrc, payload):
        """Encode the RTP packet with header fields and payload."""
        timestamp = int(time())
        header = bytearray(HEADER_SIZE)

        # First byte: V(2bit), P(1), X(1), CC(4)
        header[0] = (version << 6) | (padding << 5) | (extension << 4) | (cc & 0x0F)
        # Second byte: M(1) + PT(7)
        header[1] = (marker << 7) | (pt & 0x7F)
        # Sequence number (2 bytes)
        header[2] = (seqnum >> 8) & 0xFF
        header[3] = seqnum & 0xFF
        # Timestamp (4 bytes)
        header[4] = (timestamp >> 24) & 0xFF
        header[5] = (timestamp >> 16) & 0xFF
        header[6] = (timestamp >> 8) & 0xFF
        header[7] = timestamp & 0xFF
        # SSRC (4 bytes)
        header[8] = (ssrc >> 24) & 0xFF
        header[9] = (ssrc >> 16) & 0xFF
        header[10] = (ssrc >> 8) & 0xFF
        header[11] = ssrc & 0xFF

        self.header = header
        # payload should be bytes
        self.payload = payload if isinstance(payload, (bytes, bytearray)) else payload.encode() 
