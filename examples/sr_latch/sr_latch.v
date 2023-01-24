`include "7402.v"

module sr_latch
(
   input _Reset,
   input _Set,
   output _Q
);


   assign plus5V = 1;
   wire _nQ;
   assign GND = 0;
   wire unconnected__U1_Pad10_;
   wire unconnected__U1_Pad13_;


   D1 _D1(GND, _Q);

   SW1 _SW1(plus5V, _Reset);

   SW2 _SW2(plus5V, _Set);

   U1 _U1(_Q, _Reset, _nQ, _nQ, _Q, _Set, GND, GND, unconnected__U1_Pad10_, GND,
    GND, unconnected__U1_Pad13_);


endmodule


module D1(
   inout K,
   inout A);

endmodule

module SW1(
   inout _1,
   inout _2);

endmodule

module SW2(
   inout _1,
   inout _2);

endmodule

module U1(
   output _1,
   input _2,
   input _3,
   output _4,
   input _5,
   input _6,
   input _8,
   input _9,
   output _10,
   input _11,
   input _12,
   output _13);

ttl_7402 U1(_2, _3, _5, _6, _8, _9, _11, _12, _1, _4, _10, _13);

endmodule

