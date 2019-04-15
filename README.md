# Lora Firmware Update Python Repo
Python code for the firmware updating protocol I wrote as part of my Master's thesis  
Includes a working Class A update server and some simulation tools.

## Servers  
Servers for:
  - Piggybacked Selective Repeat ARQ Adapted for Class A and B (An adaptation of the protocol designed for Class A by Kevin O'Sullivan of TCD)
  - True Selective Repeat Server for Class B (may also work with Class A without modification, but that is untested) 
  - NACKed Piggybacked Selective Repeat same as protocol 1, except for its use of negative acknowledgement over positive acknowledgement.
    
Servers currently only serve one update to one device and need to be restarted to restart updates  
  
## Device Emulation  
Several emulated devices of Class A and B designed to accurately reproduce the behaviour of real LoraWAN nodes of the same class. Changeable spreading factor packet loss rate and duty cycle restrictions simulated.  
As results come in, this section will be updated with comparisons between emulated and real devices.
