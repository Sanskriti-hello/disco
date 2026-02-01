import React from "react";
import Frame22 from "./pages/Frame22.jsx";

const App = (props) => {
  // Pass all props from App down to Frame22
  return <Frame22 {...props} />;
};

export default App;
