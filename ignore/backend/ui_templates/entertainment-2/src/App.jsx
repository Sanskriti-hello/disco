import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Frame27 from "./pages/Frame27.jsx";
import Tooltip from "./pages/Tooltip.jsx";
import Avatar from "./pages/Avatar.jsx";
import Searchbar from "./pages/Searchbar.jsx";

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Frame27 />} />
        <Route path="/Tooltip" element={<Tooltip />} />
        <Route path="/Avatar" element={<Avatar />} />
        <Route path="/Searchbar" element={<Searchbar />} />
      </Routes>
    </Router>
  );
};

export default App;
