import {useState} from "react";
import {ChevronDonwn1} from"./ChevronDonwn1";
import { ChevronLeft} from "./ChevronLeft";
import { ChevronRight } from "./ChevronRight";

const WEEKDAY_LABELS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];
const CALENDER_WEEKS = [
    [
        {day:null, isCurrentMonth:false},
        {day:1, isCurrentMonth:true, isSelected:true},
        {day:2, isCurrentMonth:true},
        {day:3, isCurrentMonth:true},
        {day:4, isCurrentMonth:true},
        {day:5, isCurrentMonth:true},
        {day:6, isCurrentMonth:true},
    ],
    [
        {day:7, isCurrentMonth:true},
        {day:8, isCurrentMonth:true},
        {day:9, isCurrentMonth:true},
        {day:10, isCurrentMonth:true},
        {day:11, isCurrentMonth:true},
        {day:12, isCurrentMonth:true},
        {day:13, isCurrentMonth:true},
    ],
    [
        {day:14, isCurrentMonth:true},
        {day:15, isCurrentMonth:true},
        {day:16, isCurrentMonth:true},
        {day:17, isCurrentMonth:true},
        {day:18, isCurrentMonth:true},
        {day:19, isCurrentMonth:true},
        {day:20, isCurrentMonth:true},
    ],
    [
        {day:21, isCurrentMonth:true},
        {day:22, isCurrentMonth:true},
        {day:23, isCurrentMonth:true},
        {day:24, isCurrentMonth:true},
        {day:25, isCurrentMonth:true},
        {day:26, isCurrentMonth:true},
        {day:27, isCurrentMonth:true},
    ],
    [
        {day:28, isCurrentMonth:true},
        {day:29, isCurrentMonth:true},
        {day:30, isCurrentMonth:true},
        {day:31, isCurrentMonth:true},
        {day:1 , isCurrentMonth:false},
        {day:2 , isCurrentMonth:false},
        {day:3 , isCurrentMonth:false},
        {day:4 , isCurrentMonth:false},
    ],
];

export const DatePickerSection = (): JSX.Element => {
    const [selectedMonth, setSelectedMonth] = useState("February");
    const[selectedYear, setSelectedYear] = useState(2026);

    return(
        <div classname="top -[559px] left-[127px] w-[391px] h-[334px] absolute flex">
            <div className="felx w-[391px h-[334px] relative flex-colitems -center pt-[var(--size-space-400)] pr-[var(--size-space-400)] pb-[var(--size-space-400)] pl-[var(--size-space-400)] gap-[var(--size-space-200)] bg-white box-border border-[1px] border-solid border-[var(--color-outline-variant)] rounded-[var(--size-radius-large)]">
                <dic className="felx items-center gap-[var(--size-space-400)] relative self-stretch w-full flex-[0_0_auto] z-[1]">
                    <button
                        className="inline-flex items-center justify-center pt-[var(--size-spze-200)] pr-[var(--size-space-200)] pb-[var(--size-space-200)] pl-[var(--size-space-200)] relative flex-[0_0_auto] rounded-[var(--typography-primitives-scale-06)] overflow-hidden"
                        aria-label="Previous month"
                    >
                        <ChevronLeft className ="!relative !w-5 !h-5" />
                    </button>
                    <div className="flex items-start gap-[var(--size-space-200)] relative felx-1 grow">
                        <div className="flex flex-col items-start gap-[var(--size-space-200)] relative flex-1 grow z-[1]">
                            <div className="flex items-center gap-[var(--size-space-200)] pt-[var(--size-space-150)] pr-[var(--size-space-150)] pb-[var(--size-space-150)] pl-[var(--size-space-150)] relative self-stretch w-full flex-[0_0_auto] mt-[-1.00px] mb-[-1.00px] ml-[-1.00px] mr-[-1.00px] bg-color-background-default-default rounded-[var(--size-radium-200)] border border-solid border-color-border-default-default">
                                <label htmlFor="month-select" className="sr-only">
                                    Select month
                                </label>
                                <select
                                    id="month-select"
                                    value={selectedMonth}
                                    onChange={(e) => setSelectedMonth(e.target.value)}
                                    className="relative flex-1 mt-[10.50px] font-single-line-body-base font-[number:var(--single-line-body-base-font-weight)] text-color-text-default-default text-[length:var(--single-line-body-base-font-size)] tracking-[var(--single-line-body-base-letter-spacing)] leading-var(--single-line-body-base-line-height)] [font-style:var(--single-line-body-base-font-style)] bg-transparent border-none outline-none appearance-none curson-pointer"
                                >
                                    <option value="January">January</option>
                                    <option value="February">February</option>
                                    <option value="March">March</option>
                                    <option value="April">April</option>
                                    <option value="May">May</option>
                                    <option value="June">June</option>
                                    <option value="July">July</option>
                                    <option value="August">August</option>
                                    <option value="September">September</option>
                                    <option value="October">October</option>
                                    <option value="November">November</option>
                                    <option value="December">December</option>
                                </select>
                                <ChevronDown1 classname="!relative !w-4 !h-4 pointer-events-none" />
                            </div>
                        </div>

                        <div className="flex flex-col items-start gap-[var(--size-space-200)] relative flex-1 grow z-0">
                            <div className="flex items-center gap-[var(--size-space-200)] pt-[var(--size-space-150)] pr-[var(--size-space-150)] pb-[var(--size-space-150)] pl-[var(--size-space-150)] relative self-stretch w-full flex-[0_0_auto] mt-[-1.00px] mb-[-1.00px] ml-[-1.00px] mr-[-1.00px] bg-color-background-default-default rounded-[var(--size-radius-200)] border border-solid border-color-border-default-default">
                                <label htmlFor="year-select" className="sr-only">
                                    Select year
                                </label>
                                <select
                                    id="year-select"
                                    value={selectedYear}
                                    onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                                    className="relative flex-1 mt-[-0.50px] font-single-line-body-base font-[number:var(--single-line-body-base-font-weight)] text-color-text-default-default text-[length:var(--single-line-body-base-font-size)] tracking-[var(--single-line-body-base-letter-spacing)] leading-var(--single-line-body-base-line-height)] [font-style:var(--single-line-body-base-font-style)] bg-transparent border-none outline-none appearance-none curson-pointer"
                                >
                                    <option value={2023}>2023</option>
                                    <option value={2024}>2024</option>
                                    <option value={2025}>2025</option>
                                    <option value={2026}>2026</option>
                                    <option value={2027}>2027</option>
                                </select>
                                <ChevronDown1 classname="!relative !w-4 !h-4 pointer-events-none" />
                            </div>
                        </div>
                    </div>

                    <button
                        className="inline-flex items-center justify-center pt-[var(--size-space-200)] pr-[var(--size-space-200)] pb-[var(--size-space-200)] pl-[var(--size-space-200)] relative flex-[0_0_auto] rounded-[var(--typography-primitives-scale-06)] overflow-hidden"
                        aria-label="Next month"
                    >
                        <ChevronRight className ="!relative !w-5 !h-5" />
                    </button>
                </div>

                <div className="inline-flex flex-col items-center pt-[var(--size-space-400)] pb-0 px-0 relative flex-[0_0_auto z-0">
                    <div className="flex items-center justify-center gap-px relative self-stretch w-full flex-[0_0_auto]">
                        {WEEKDAY_LABELS.map((label, index) => (
                            <div
                                key={index}
                                className="flex items-center justify-center relative flex-1 grow"
                            >
                                <div className="relative flex items-center justify-center w-fit mt-[-1.00px] font-text-extra-small font-[number:var(--text-extra-small-font-weight)] text-color-text-secondary text-[length:var(--text-extra-small-font-size)] text-center tracking-[var(--text-extra-small-letter-spacing)] leading-[var(--text-extra-small-line-height)] whitespace-nowrap [font-style:var(--text-extra-small-font-style)]">
                                    {label}
                                </div>
                            </div>
                        ))}
                    </div>
                    
                    <div className="inline-felx flex-col items-center gap-px relative flex=[0_0_auto]">
                        {CALENDER_WEEKS.map((week, weekIndex) => (
                            <div
                                key={weekIndex}
                                className="inline-flex gap-px items-center flex-[0_0_auto]"
                                style={{zIndex: CALENDER_WEEKS.length - weekIndex}}
                            >
                                {week.map((dayData, dayIndex) => {
                                    const {day, isCurrentMonth, isSelected} = dayData;
                                    let bgClass ="";
                                    let textColor = "text-color-text-default-default";
                                    if(isSelected){
                                        bgClass = "bg-color-background-brand-default";
                                        textColor = "text-color-text-brand-on-default";
                                    }else if(isInRange){
                                        bgClass = "bg-color-background-default-secondary";
                                        textColor = "text-color-text-brand-default";
                                    }else if(!isCurrentMonth){
                                        textColor = "text-color-text-disabled";
                                    }

                                    return(
                                        <button
                                            key={dayIndex}
                                            className={`flex w-10 h-10 items-center justify-center pt-[var(--size-space-400)] pr-[var(--size-space-400)] pb-[var(--size-space-400)] pl-[var(--size-space-400)] relative rounded-[var(--size-radius-200)] ${bgClass} ${textColor}`}
                                            aria-label={day ? `Day ${day}` : undefined}
                                        >
                                            {day!==null && (
                                                <div
                                                    className={`${textColor} relative flex items-center justify-center w-fit mt-[-8.00px] mb-[-6.00px] font--body-base font-[number:var(--body-base-font-weight)] text-[length:var(--body-base-font-size)] text-center tracking-[var(--body-base-letter-spacing)] leading-[var(--body-base-line-height)] whitespace-nowrap [font-style:var(--body-base-font-style)]`}
                                                    style={{
                                                        marginLeft:
                                                            day>=10 ? "-5px" : day>= 2? "-1px" : "0",
                                                        marginRight:
                                                            day>=10 ? "-5px" : day>=2 ? "-1px" : "0",
                                                    }}
                                                >
                                                    {day}
                                                </div>
                                            )}
                                        </button>
                                    )
                                })}
                            </div>
                        ))}
                    </div>  
                </div>
        </div>
    )