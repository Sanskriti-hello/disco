import { Home } from "./Home";
import { Info } from "./Info";
import { User } from "./User";
import rectangle1 from "./rectangle-1.png";
import rectangle79 from "./rectangle-79.png";

export const Frame = (): JSX.Element => {
  return (
    <div className="bg-white w-full min-w-[1440px] min-h-[1024px] overflow-hidden relative">
      <header className="absolute top-0 left-0 w-[1440px] h-[118px]">
        <div className="w-full h-full object-cover">
          <img
            className="w-full h-full object-cover"
            alt="Header background with abstract pattern"
            src={rectangle1}
          />
        </div>
        <h1 className="absolute top-[57px] left-[calc(50.00%_-_425.5px)] w-[851px] h-[42px] [font-family:'Roboto-Bold',Helvetica] font-bold text-white text-[55px] tracking-[0] leading-[normal]">
          SINU
        </h1>
      </header>

      <nav className="absolute top-[131px] right-[120px] flex gap-[20px]" aria-label="Main navigation">
        <Home className="!w-8 !h-8" aria-label="Home" />
        <User className="!w-8 !h-8" aria-label="User profile" />
        <Info className="!w-8 !h-8" aria-label="Information" />
      </nav>

      <main className="absolute top-[218px] left-[120px] w-[1200px] h-[755px]">
        <div className="flex">
          <div className="w-[690px] h-[755px] bg-[#2eafab] rounded-[20px_0px_0px_20px]">
            <div className="w-[510px] h-[755px] bg-[#2eafab] rounded-[20px_0px_0px_20px]" />
          </div>
        </div>

        <div className="absolute top-[441px] left-[714px] w-[486px] h-[314px]">
          <img
            className="absolute top-0 left-0 w-full h-full object-cover"
            alt="Decorative texture background"
            src={rectangle79}
          />
        </div>

        <article className="absolute top-[137px] left-[33px] w-[624px] h-[171px]">
          <h2 className="w-[171px] [font-family:'Roboto-Bold',Helvetica] font-bold text-white text-[55px] tracking-[0] leading-[normal]">
            Summary
          </h2>
        </article>

        <p className="w-[624px] [font-family:'Inter-Regular',Helvetica] font-normal text-white text-[55px] tracking-[0] leading-[normal]">
          text
        </p>
      </main>
    </div>
  );
};