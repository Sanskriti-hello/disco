import { DatePickerSection } from "./DatePickerSection";
import { FAQAccordionSection } from "./FAQAccordionSection";
import { Home } from "./Home";
import { Icon } from "./Icon";
import { IconComponentNode } from "./IconComponentNode";
import { Info } from "./Info";
import { MenuListSection } from "./MenuListSection";
import { PhotoGallerySection } from "./PhotoGallerySection";
import { User } from "./User";
import caret from "./caret.svg";
import divider from "./divider.svg";
import rectangle1 from "./rectangle-1.png";

export const FrameScreen = (): JSX.Element => {
  return (
    <div className="bg-white w-full min-w-[1440px] min-h-[1024px] relative">
      <img
        className="absolute top-0 left-0 w-[1440px] h-[180px]"
        alt="Rectangle"
        src={rectangle1}
      />

      <Home className="!absolute !top-[129px] !left-[1072px] !w-8 !h-8" />
      <User className="!absolute !top-[129px] !left-[1164px] !w-8 !h-8" />
      <Info className="!absolute !top-[129px] !left-[1256px] !w-8 !h-8" />

      <h1 className="absolute top-11 left-[225px] w-[223px] h-[95px] flex items-center justify-center [font-family:'Roboto-Bold',Helvetica] font-bold text-black text-[64px] tracking-[0.10px] leading-5">
        Travel
      </h1>

      <PhotoGallerySection />

      <div className="flex flex-col max-w-[720px] w-[360px] h-[93px] items-start absolute top-[427px] left-[145px] bg-[#f8b63b] rounded-[28px]">
        <header className="flex h-14 items-center justify-center gap-1 p-1 relative self-stretch w-full bg-[#ece6f0] rounded-[28px_28px_0px_0px]">
          <div className="flex w-12 h-12 items-center justify-center relative">
            <div className="flex flex-col w-10 items-center justify-center relative rounded-[100px] overflow-hidden">
              <div className="flex h-10 items-center justify-center relative self-stretch w-full">
                <Icon className="!relative !w-6 !h-6" />
              </div>
            </div>
          </div>

          <div className="flex flex-col items-start justify-center gap-2.5 relative flex-1 self-stretch grow">
            <div className="inline-flex h-6 items-center gap-px px-0 py-2.5 relative">
              <input
                className="relative flex items-center justify-center w-fit mt-[-11.00px] mb-[-9.00px] font-m3-body-large font-[number:var(--m3-body-large-font-weight)] text-[#1d1b20] text-[length:var(--m3-body-large-font-size)] tracking-[var(--m3-body-large-letter-spacing)] leading-[var(--m3-body-large-line-height)] whitespace-nowrap [font-style:var(--m3-body-large-font-style)] [background:transparent] border-[none] p-0"
                placeholder="Input text"
                type="text"
                aria-label="Search input"
              />

              <img
                className="relative w-px h-[17px] mt-[-6.50px] mb-[-6.50px] mr-[-0.50px]"
                alt="Caret"
                src={caret}
              />
            </div>
          </div>

          <div className="flex w-12 h-12 items-center justify-center relative">
            <div className="flex flex-col w-10 items-center justify-center relative rounded-[100px] overflow-hidden">
              <div className="flex h-10 items-center justify-center relative self-stretch w-full">
                <IconComponentNode className="!relative !w-6 !h-6" />
              </div>
            </div>
          </div>
        </header>

        <div className="flex flex-col items-start justify-center relative self-stretch w-full flex-[0_0_auto]">
          <img
            className="relative self-stretch w-full h-px object-cover"
            alt="Divider"
            src={divider}
          />
        </div>

        <div className="relative self-stretch w-full h-[72px] mb-[-36.00px]" />
      </div>

      <MenuListSection />

      <FAQAccordionSection />

      <DatePickerSection />
    </div>
  );
};
