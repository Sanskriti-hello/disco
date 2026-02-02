import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Frame22 from "./pages/Frame22.jsx";
import Frame25 from "./pages/Frame25.jsx";
import TextCode from "./pages/TextCode.jsx";
import TextCode2 from "./pages/TextCode2.jsx";

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Frame22 />} />
        <Route path="/Frame25" element={<Frame25 />} />
        <Route path="/TextCode" element={<TextCode />} />
        <Route path="/TextCode2" element={<TextCode2 />} />
      </Routes>
    </Router>
  );
};

export default App;
