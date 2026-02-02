import React from "react";
const Tooltip = () => {
  return (
    <>
      <div
        id="_69_514__Tooltip"
        className="absolute bg-white border shadow-[0.0px_1.0px_4.0px_0.0px_rgba(12,12,13,0.05),0.0px_1.0px_4.0px_0.0px_rgba(12,12,13,0.10)] h-[calc(298.0px-12px-12px)] w-[calc(410.0px-12px-12px)] flex flex-col justify-start items-center flex-nowrap px-3 py-2 rounded-lg border-[#0a89e0ff] border-solid"
      >
        <img
          id="I69_514_352_6314__Beak"
          src="assets/images/beak.svg"
          alt="Beak"
          className="absolute rotate-[45.00deg] left-[calc(50%+-0.00px)] bottom-[-2.05px]"
        />
        <img
          id="I69_514_352_6313__Beak__Stroke_"
          src="assets/images/beak_stroke.svg"
          alt="Beak__Stroke_"
          className="absolute rotate-[45.00deg] left-[calc(50%+-0.00px)] bottom-[-2.05px]"
        />
        <span
          id="I69_514_368_11411__Title"
          className="flex justify-center text-center items-start h-[22.00px] w-[35.00px] relative"
        >
          <span
            className="whitespace-nowrap bg-black bg-clip-text text-transparent not-italic text-[16.0px] font-semibold leading-[140.00%]"
            style={{
              fontFamily: "Inter",
            }}
          >
            Title
          </span>
        </span>
        <span
          id="I69_514_368_11412__Body_text"
          className="flex justify-center text-center items-start h-[20.00px] w-[64.00px] relative"
        >
          <span
            className="whitespace-nowrap bg-black bg-clip-text text-transparent not-italic text-[14.0px] font-normal leading-[140.00%]"
            style={{
              fontFamily: "Inter",
            }}
          >
            Body text
          </span>
        </span>
      </div>
    </>
  );
};
export default Tooltip;
