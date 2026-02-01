import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Frame15 from "./pages/Frame15.jsx";
import Frame16 from "./pages/Frame16.jsx";
import Frame14 from "./pages/Frame14.jsx";
import Frame17 from "./pages/Frame17.jsx";

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Frame15 />} />
        <Route path="/Frame16" element={<Frame16 />} />
        <Route path="/Frame14" element={<Frame14 />} />
        <Route path="/Frame17" element={<Frame17 />} />
      </Routes>
    </Router>
  );
};

export default App;
