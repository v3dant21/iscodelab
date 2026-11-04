const images: Record<string, string> = {
  'dum chicken biryani': '/images/dumhouse-biryani.png',
  'hyderabadi mutton biryani': '/images/mutton-biryani.png',
  'paneer dum biryani': '/images/paneer-biryani.png',
  'chicken 65': '/images/chicken-65.png',
  'mirchi ka salan': '/images/mirchi-salan.png',
  'double ka meetha': '/images/double-meetha.png',
};

export function foodImage(name: string) {
  return images[name.toLowerCase()];
}

export function FoodImage({ name, className = '' }: { name: string; className?: string }) {
  const source = foodImage(name);
  return source ? <img className={className} src={source} alt={`Illustrative ${name}`} width={512} height={512} loading="lazy" /> : null;
}
