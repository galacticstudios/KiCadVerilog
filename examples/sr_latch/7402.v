// Quad 2-input NOR gate

module ttl_7402
(
  input a1, b1, a2, b2, a3, b3, a4, b4,
  output o1, o2, o3, o4
);

assign o1 = ~(a1 | b1);
assign o2 = ~(a2 | b2);
assign o3 = ~(a3 | b3);
assign o4 = ~(a4 | b4);

endmodule
