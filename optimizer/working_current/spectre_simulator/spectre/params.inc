* Parameters for OPA_SR Netlist (180nm Process)
* Transistor Widths (W) and Lengths (L)
.param
* PMOS Transistors (VDD-connected)
+ w7  = 10u     l7  = 0.18u    * M7: Output PMOS (Push-Pull Stage)
+ w12 = 2u      l12 = 0.18u    * M1-M2: Differential Pair PMOS
+ w5  = 4u      l5  = 0.18u    * M5: Tail Current Source PMOS
+ w8  = 2u      l8  = 0.18u    * M8: Bias PMOS (Diode-Connected)

* NMOS Transistors (GND-connected)
+ w6  = 5u      l6  = 0.18u    * M6: Output NMOS (Push-Pull Stage)
+ w34 = 2u      l34 = 0.18u    * M3-M4: Current Mirror NMOS

* Compensation Capacitor
+ cm  = 1pF                    * Miller Capacitor (C1)
+vdd =1.8