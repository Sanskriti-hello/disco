import { Star } from "./Star";

interface MenuItem {
  label: string;
  description: string;
  shortcut: string;
}

export const MenuListSection = (): JSX.Element => {
  const topMenuItems: MenuItem[] = [
    {
      label: "Menu Label",
      description: "Menu description.",
      shortcut: "⌘A",
    },
    {
      label: "Menu Label",
      description: "Menu description.",
      shortcut: "⌘A",
    },
    {
      label: "Menu Label",
      description: "Menu description.",
      shortcut: "⌘A",
    },
  ];

  const bottomMenuItems: MenuItem[] = [
    {
      label: "Menu Label",
      description: "Menu description.",
      shortcut: "⌘A",
    },
    {
      label: "Menu Label",
      description: "Menu description.",
      shortcut: "⌘A",
    },
  ];

  return (
    <nav
      className="top-[415px] left-[562px] w-[399px] h-[476px] absolute bg-color-default-default rounded-lg overflow-hidden"
      aria-label="Menu List"
    >
      <div className="flex w-[399px] h-[476px] relative flex-col items-start">
        <header className="relative self-stretch mt-[-1.00px] font-heading">
          <div className="relative self-stretch font-body-strong text-default-default">
            Heading
          </div>
        </header>

        <div className="flex flex-col items-center justify-center relative self-stretch w-full h-px bg-color-border-default" />
        <div className="flex flex-col items-center justify-center relative self-stretch w-full h-px bg-color-border-default">
          {topMenuItems.map((item, index) => (
            <li
              key={index}
              className="flex w-[285px] items-start gap-[var(--size-space-300)] pl-[var(--size-space-200)] pr-[var(--size-space-400)] pb-[var(--size-space-200)] pt-[var(--size-space-200)] self-stretch w-full relative flex-1 grow"
            >
              <Star className="relative w-5 h-5" aria-hidden="true" />
              <div className="flex flex-col items-center justify-between self-stretch w-full relative flex-1 mt-[-1.00px]">
                <span className="relative flex-1 mt-[-1.00px]">
                  {item.label}
                </span>
                <kbd className="inline-flex items-center justify-center">
                  <span className="relative w-fit mt-[-1.00px]">
                    {item.shortcut}
                  </span>
                </kbd>
              </div>
              <p className="relative self-stretch w-full h-px bg-color-border-default">
                {item.description}
              </p>
            </li>
          ))}
        </div>

        <div className="flex flex-col items-center justify-center relative self-stretch w-full h-px bg-color-border-default" />
        <ul className="flex flex-col items-start relative self-stretch w-full fontSizeRemap">
          {bottomMenuItems.map((item, index) => (
            <li
              key={index}
              className="flex items-start gap-[var(--size-space-300)]"
            >
              <Star className="relative w-5 h-5" aria-hidden="true" />
              <div className="flex flex-col items-center justify-between self-stretch w-full relative flex-1 mt-[-1.00px]">
                <span className="relative flex-1 mt-[-1.00px]">
                  {item.label}
                </span>
                <kbd className="inline-flex items-center justify-center">
                  <span className="relative w-fit mt-[-1.00px]">
                    {item.shortcut}
                  </span>
                </kbd>
              </div>
              <p className="relative self-stretch w-full h-px bg-color-border-default">
                {item.description}
              </p>
            </li>
          ))}
        </div>
      </div>
    </nav>
  );
};