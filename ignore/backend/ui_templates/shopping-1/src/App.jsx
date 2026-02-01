import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Frame1 from "./pages/Frame1.jsx";

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Frame1 />} />
      </Routes>
    </Router>
  );
};

export default App;
