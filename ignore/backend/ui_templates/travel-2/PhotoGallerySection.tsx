export const PhotoGallerySection = (): JSX.Element => {
  const galleryItems = [
    { id: 1, description: "Photo desc" },
    { id: 2, description: "Photo desc" },
    { id: 3, description: "Photo desc" },
    { id: 4, description: "Photo desc" },
    { id: 5, description: "Photo desc" },
    { id: 6, description: "Photo desc" },
  ];

  return (
    <section
      className="grid grid-cols-6 grid-rows-2 w-[120px] h-[171px] left-[105px] bg-[#f8bc38] rounded-[20px] absolute top-[171px] gap-[110px_33px] pt-[27px] pb-[232px] px-[22px] absolute top-[0px] left-[105px] bg-[#f8bc38] rounded-[20px]"
      aria-label="Photo Gallery"
    >
      {galleryItems.map((item, index) => (
        <figure
          key={`photo-${item.id}`}
          className={`relative row-[1_/_2] col-[${(index + 1)_/_${(index + 2)}] w-[170px] h-[108px] bg-white`}
          aria-label={item.description}
        >
        </figure>
      ))}
      {galleryItems.map((item, index) => (
        <figcaption
          key={`desc-${item.id}`}
          className={`${index === 0 ? "" : `col-[${(index + 1)_/_${(index + 2)}] } relative flex items-center justify-center row-[2_/_3] col-[1_/_2] ${index === 0 ? "row-[2_/_3] col-[1_/_2]" : ""} w-[165px] h-[18px] font-m3-body-large font-[number:var(--m3-body-large-font-weight)] text-white text-[length:var(--m3-body-large-font-size)] tracking-[var(--m3-body-large-letter-spacing)] leading-[var(--m3-body-large-line-height)] whitespace-nowrap [font-style:var(--m3-body-large-font-style)]`}
        >
          {item.description}
        </figcaption>
      ))}
    </section>
  );
};