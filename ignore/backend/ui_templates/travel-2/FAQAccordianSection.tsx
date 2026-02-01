import { useState} from "react";
import {ChevronDown} from "./ChevronDown";
import {ChevronUp} from "./ChevronUp";

interface FAQItem {
    id: number;
    title: string;
    answer: string;
}

export const FAQAccordionSectionReact = (): JSX.Element => {
    const [openItemId, setOpenItemId] = useState<number | null>(0);
    const faqItems: FAQItem[] = [
        {
            id: 0,
            title: "Title",
            answer:
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
        },
        {
            id: 1,
            title: "Title",
        },
        {
            id: 2,
            title: "Title",
        },
        {
            id: 3,
            title: "Title",
        },
        {
            id: 4,
            title: "Title",
        },
    ];

    const toggleItem = (id: number) => {
        setOpenItemId(openItemId === id ? null : id);
    };

    return (
        <section
            className="flex flex-col w-[294px] h-[476px] items-start gap-[var(--size-space-400)] absolute top-[415px] left=[1004px] rounded-[20px] border-[15px] border-solid border-[#f8b63b]"
            aria-label="lequently Asked Questions"
        >
            {faqItems.map((item) => (
                const isOpen = openItemId === item.id,
            
                return (
                    <div
                        key={item.id}
                        className = {'flex flex-col items-start ${isOpen ? "gap-[var(--size-space-200)]" :""} pt-[var(--size-padding-lg)] pr-[var(--size-padding-lg)] pb-[var(--size-padding-lg)] pl-[var(--size-padding-lg)] relative self-stretchcw-full flex-[0_0_auto] $(isOpen ? "bg-color-background-default-default" : "bg-color-background-default-secondary"} rounded-[var(--size-radius-200)] border border-solid border-color-border-default-default'}
                    >
                        <button
                            className="flex item-center gap-[var(--size-space-200)] relative self-stretch w-full flex-[0_0_auto] bg-transparent border-0 p-0 cursor-pointer text-left"
                            onClick={() => toggleItem(item.id)}
                            aria-expanded={isOpen}
                            aria-controls={`faq-answer-${item.id}`}
                        >
                            <h3 className="relative flex-1 mt-[-1.00px] font-body-strong font-[number:var(--body-strong-font-weight)] text-color-text-default-default text-[length:var(--body-strong-font-size)] tracking-[var(--body-strong-letter-spacing)] leading-[var(--body-strong-line-height)] [font-style:var(--body-strong-font-style)] m-0">
                                {item.title}
                            </h3>

                            {isOpen ? (
                                <ChevronUp className="!relative !w-5 !h-5" aria-hidden="true" />
                            ) : (
                                <ChevronDown className="!relative !w-5 !h-5" aria-hidden="true" />
                            )}
                        </button>

                        {isOpen && item.answer && (
                            <div
                                id={`faq-answer-${item.id}`}
                                className="justify-center self-stretch w-full flex-[0_0_auto] flex item-center relative"
                                role="region"
                            >
                                <p className="relative flex items-center justify-center flex-1 mt-[-1.00px] font-body-base font-[number:var(--body-base-font-weight)] text-color-text-default-default text-[length:var(--body-base-font-size)] tracking-[var(--body-base-letter-spacing)] leading-[var(--body-base-line-height)] [font-style:var(--body-base-font-style)] m-0">
                                    {item.answer}
                                </p>
                            </div>
                        )
                            }
                    </div>
        </section>
    )