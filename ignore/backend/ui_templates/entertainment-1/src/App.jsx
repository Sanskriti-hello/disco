import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Frame26 from "./pages/Frame26.jsx";
import Text from "./pages/Text.jsx";
import Text2 from "./pages/Text2.jsx";
import ButtonGroup from "./pages/ButtonGroup.jsx";
import Bookmark from "./pages/Bookmark.jsx";
import Favorite from "./pages/Favorite.jsx";

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Frame26 />} />
        <Route path="/Text" element={<Text />} />
        <Route path="/Text2" element={<Text2 />} />
        <Route path="/ButtonGroup" element={<ButtonGroup />} />
        <Route path="/Bookmark" element={<Bookmark />} />
        <Route path="/Favorite" element={<Favorite />} />
      </Routes>
    </Router>
  );
};

export default App;
