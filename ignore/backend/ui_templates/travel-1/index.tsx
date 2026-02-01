import { useState } from "react";
import { ChevronLeft } from "./ChevronLeft";
import { ChevronRight } from "./ChevronRight";
import { Home } from "./Home";
import { Info } from "./Info";
import { User } from "./User";
import rectangle1 from "./rectangle-1.png";

export const Frame = (): JSX.Element => {
  const [selectedMonth, setSelectedMonth] = useState("Sep");
  const [selectedYear, setSelectedYear] = useState("2025");

  const weekDays = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];

  const calendarWeeks = [
    [
      { day: "", disabled: false },
      { day: "1", disabled: false },
      { day: "2", disabled: false },
      { day: "3", disabled: false },
      { day: "4", disabled: false },
      { day: "5", disabled: false },
      { day: "6", disabled: false },
    ],
    [
      { day: "7", disabled: false },
      { day: "8", disabled: false },
      { day: "9", disabled: false, selected: true },
      { day: "10", disabled: false, highlighted: true },
      { day: "11", disabled: false, highlighted: true },
      { day: "12", disabled: false, highlighted: true },
      { day: "13", disabled: false, selected: true },
    ],
    [
      { day: "14", disabled: false },
      { day: "15", disabled: false },
      { day: "16", disabled: false },
      { day: "17", disabled: false },
      { day: "18", disabled: false },
      { day: "19", disabled: false },
      { day: "20", disabled: false },
    ],
    [
      { day: "21", disabled: false },
      { day: "22", disabled: false },
      { day: "23", disabled: false },
      { day: "24", disabled: false },
      { day: "25", disabled: false },
      { day: "26", disabled: false },
      { day: "27", disabled: false },
    ],
    [
      { day: "28", disabled: false },
      { day: "29", disabled: false },
      { day: "30", disabled: false },
      { day: "1", disabled: true },
      { day: "2", disabled: true },
      { day: "3", disabled: true },
      { day: "4", disabled: true },
    ],
  ];

  const photoGalleryItems = [
    { id: 1, description: "Photo desc" },
    { id: 2, description: "Photo desc" },
    { id: 3, description: "Photo desc" },
    { id: 4, description: "Photo desc" },
  ];

  return (
    <div className="bg-white w-full min-w-[1440px] min-h-[1024px] relative">
      <header>
        <img
          className="absolute top-0 left-0 w-[1440px] h-[180px] object-cover"
          alt="Travel destination map"
          src={rectangle1}
        />

        <h1 className="absolute top-[55px] left-[168px] w-[223px] h-[95px] flex items-center justify-center [font-family:'Inter-Bold',Helvetica] font-bold text-black text-[64px] tracking-[0.10px] leading-5">
          Travel
        </h1>

        <nav
          className="absolute top-[126px] right-[140px] flex gap-[92px]"
          aria-label="Main navigation"
        >
          <button type="button" aria-label="Home">
            <Home className="!w-8 !h-8" />
          </button>
          <button type="button" aria-label="User profile">
            <User className="!w-8 !h-8" />
          </button>
          <button type="button" aria-label="Information">
            <Info className="!w-8 !h-8" />
          </button>
        </nav>
      </header>

      <main>
        <section
          className="absolute top-[202px] left-[120px] w-[349px] h-[351px] flex bg-[#3ba9f8] rounded-[20px]"
          aria-label="Calendar"
        >
          <div className="inline-flex mt-5 w-[318px] h-[308px] ml-[15px] relative flex-col items-center pt-[var(--size-space-400)] pr-[var(--size-space-400)] pb-[var(--size-space-400)] pl-[var(--size-space-400)] bg-color-background-default-default rounded-[var(--size-radius-400)] border border-solid border-color-border-default-default">
            <div className="flex items-center gap-[var(--size-space-400)] relative self-stretch w-full flex-[0_0_auto] z-[1]">
              <button
                type="button"
                className="inline-flex items-center justify-center pt-[var(--size-space-200)] pr-[var(--size-space-200)] pb-[var(--size-space-200)] pl-[var(--size-space-200)] relative flex-[0_0_auto] rounded-[var(--typography-primitives-scale-06)] overflow-hidden"
                aria-label="Previous month"
              >
                <ChevronLeft className="!relative !w-5 !h-5" />
              </button>

              <div className="flex items-start gap-[var(--size-space-200)] relative flex-1 grow">
                <div className="flex flex-col items-start gap-[var(--size-space-200)] relative flex-1 grow z-[1]">
                  <label htmlFor="month-select" className="sr-only">
                    Select month
                  </label>
                  <select
                    id="month-select"
                    value={selectedMonth}
                    onChange={(e) => setSelectedMonth(e.target.value)}
                    className="flex items-center gap-[var(--size-space-200)] pt-[var(--size-space-150)] pr-[var(--size-space-150)] pb-[var(--size-space-150)] pl-[var(--size-space-150)] relative self-stretch w-full flex-[0_0_auto] mt-[-1.00px] mb-[-1.00px] ml-[-1.00px] mr-[-1.00px] bg-color-background-default-default rounded-[var(--size-radius-200)] border border-solid border-color-border-default-default font-single-line-body-base font-[number:var(--single-line-body-base-font-weight)] text-color-text-default-default text-[length:var(--single-line-body-base-font-size)] tracking-[var(--single-line-body-base-letter-spacing)] leading-[var(--single-line-body-base-line-height)] [font-style:var(--single-line-body-base-font-style)]"
                  >
                    <option value="Sep">Sep</option>
                    <option value="Oct">Oct</option>
                    <option value="Nov">Nov</option>
                    <option value="Dec">Dec</option>
                  </select>
                </div>

                <div className="flex flex-col items-start gap-[var(--size-space-200)] relative flex-1 grow z-0">
                  <label htmlFor="year-select" className="sr-only">
                    Select year
                  </label>
                  <select
                    id="year-select"
                    value={selectedYear}
                    onChange={(e) => setSelectedYear(e.target.value)}
                    className="flex items-center gap-[var(--size-space-200)] pt-[var(--size-space-150)] pr-[var(--size-space-150)] pb-[var(--size-space-150)] pl-[var(--size-space-150)] relative self-stretch w-full flex-[0_0_auto] mt-[-1.00px] mb-[-1.00px] ml-[-1.00px] mr-[-1.00px] bg-color-background-default-default rounded-[var(--size-radius-200)] border border-solid border-color-border-default-default font-single-line-body-base font-[number:var(--single-line-body-base-font-weight)] text-color-text-default-default text-[length:var(--single-line-body-base-font-size)] tracking-[var(--single-line-body-base-letter-spacing)] leading-[var(--single-line-body-base-line-height)] [font-style:var(--single-line-body-base-font-style)]"
                  >
                    <option value="2024">2024</option>
                    <option value="2025">2025</option>
                    <option value="2026">2026</option>
                  </select>
                </div>
              </div>

              <button
                type="button"
                className="inline-flex items-center justify-center pt-[var(--size-space-200)] pr-[var(--size-space-200)] pb-[var(--size-space-200)] pl-[var(--size-space-200)] relative flex-[0_0_auto] rounded-[var(--typography-primitives-scale-06)] overflow-hidden"
                aria-label="Next month"
              >
                <ChevronRight className="!relative !w-5 !h-5" />
              </button>
            </div>

            <div className="inline-flex flex-col items-center pt-[var(--size-space-400)] pb-0 px-0 relative flex-[0_0_auto] z-0">
              <div
                className="flex items-center justify-center gap-px relative self-stretch w-full flex-[0_0_auto]"
                role="row"
              >
                {weekDays.map((day, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-center relative flex-1 grow"
                    role="columnheader"
                  >
                    <div className="relative flex items-center justify-center w-fit mt-[-1.00px] font-text-extra-small font-[number:var(--text-extra-small-font-weight)] text-color-text-default-secondary text-[length:var(--text-extra-small-font-size)] text-center tracking-[var(--text-extra-small-letter-spacing)] leading-[var(--text-extra-small-line-height)] whitespace-nowrap [font-style:var(--text-extra-small-font-style)]">
                      {day}
                    </div>
                  </div>
                ))}
              </div>

              <div
                className="inline-flex flex-col items-center gap-px relative flex-[0_0_auto]"
                role="grid"
                aria-label="Calendar dates"
              >
                {calendarWeeks.map((week, weekIndex) => (
                  <div
                    key={weekIndex}
                    className={`inline-flex items-center gap-px relative flex-[0_0_auto] z-[${4 - weekIndex}]`}
                    role="row"
                  >
                    {week.map((dayData, dayIndex) => (
                      <button
                        key={dayIndex}
                        type="button"
                        disabled={!dayData.day || dayData.disabled}
                        className={`flex w-10 h-10 items-center justify-center pt-[var(--size-space-400)] pr-[var(--size-space-400)] pb-[var(--size-space-400)] pl-[var(--size-space-400)] relative rounded-[var(--size-radius-200)] ${
                          dayData.selected
                            ? "bg-color-background-brand-default"
                            : dayData.highlighted
                              ? "bg-color-background-default-secondary"
                              : ""
                        }`}
                        aria-label={
                          dayData.day
                            ? `${dayData.day} ${selectedMonth} ${selectedYear}`
                            : undefined
                        }
                        role="gridcell"
                      >
                        {dayData.day && (
                          <span
                            className={`relative flex items-center justify-center w-fit mt-[-8.00px] mb-[-6.00px] font-body-base font-[number:var(--body-base-font-weight)] text-[length:var(--body-base-font-size)] text-center tracking-[var(--body-base-letter-spacing)] leading-[var(--body-base-line-height)] whitespace-nowrap [font-style:var(--body-base-font-style)] ${
                              dayData.selected
                                ? "text-color-text-brand-on-brand"
                                : dayData.highlighted
                                  ? "text-[color:var(--color-text-brand-default)]"
                                  : dayData.disabled
                                    ? "text-color-text-disabled-default"
                                    : "text-color-text-default-default"
                            } ${
                              dayData.day.length === 2
                                ? "ml-[-5.00px] mr-[-5.00px]"
                                : dayData.day === "2" ||
                                    dayData.day === "5" ||
                                    dayData.day === "6" ||
                                    dayData.day === "8"
                                  ? "ml-[-1.00px] mr-[-1.00px]"
                                  : dayData.day === "3" || dayData.day === "4"
                                    ? "ml-[-1.50px] mr-[-1.50px]"
                                    : dayData.day === "17"
                                      ? "ml-[-4.50px] mr-[-4.50px]"
                                      : dayData.day === "20" ||
                                          dayData.day === "22" ||
                                          dayData.day === "23" ||
                                          dayData.day === "24" ||
                                          dayData.day === "25" ||
                                          dayData.day === "26"
                                        ? "ml-[-6.00px] mr-[-6.00px]"
                                        : dayData.day === "27"
                                          ? "ml-[-5.50px] mr-[-5.50px]"
                                          : dayData.day === "30"
                                            ? "ml-[-6.50px] mr-[-6.50px]"
                                            : ""
                            }`}
                          >
                            {dayData.day}
                          </span>
                        )}
                      </button>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section
          className="absolute top-[207px] left-[504px] w-[816px] h-[171px] bg-[#3ba9f8] rounded-[20px] pt-[27px] pb-[327px] px-[22px]"
          aria-label="Photo gallery"
        >
          <div className="grid grid-cols-4 grid-rows-2 w-full h-full gap-[110px_33px]">
            {photoGalleryItems.map((item, index) => (
              <div
                key={item.id}
                className={`col-[${index + 1}_/_${index + 2}]`}
              >
                <div
                  className="relative row-[1_/_2] w-[170px] h-[100px] bg-white"
                  role="img"
                  aria-label={`Photo ${index + 1}`}
                />
                <p className="relative flex items-center justify-center row-[2_/_3] w-[165px] h-[18px] font-m3-body-large font-[number:var(--m3-body-large-font-weight)] text-white text-[length:var(--m3-body-large-font-size)] tracking-[var(--m3-body-large-letter-spacing)] leading-[var(--m3-body-large-line-height)] whitespace-nowrap [font-style:var(--m3-body-large-font-style)]">
                  {item.description}
                </p>
              </div>
            ))}
          </div>
        </section>

        <section
          className="absolute top-[401px] left-[504px] w-[816px] h-[585px] bg-[#3ba9f8] rounded-[20px]"
          aria-label="Main content area"
        ></section>

        <aside
          className="absolute top-[575px] left-[120px] w-[306px] h-[411px] bg-[#3ba9f8] rounded-[20px]"
          aria-label="Additional information"
        >
          <p className="absolute top-[29px] left-[31px] w-[250px] font-m3-body-large font-[number:var(--m3-body-large-font-weight)] text-white text-[length:var(--m3-body-large-font-size)] tracking-[var(--m3-body-large-letter-spacing)] leading-[var(--m3-body-large-line-height)] [font-style:var(--m3-body-large-font-style)]">
            text
          </p>
        </aside>
      </main>
    </div>
  );
};
