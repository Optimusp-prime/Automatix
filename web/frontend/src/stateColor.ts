/** Choose black or white by the larger relative-luminance contrast. O(1). */
export function stateTextColor(background: string): '#000000' | '#ffffff' {
  const channels = [1, 3, 5].map(start => {
    const value = parseInt(background.slice(start, start + 2), 16) / 255;
    return value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4;
  });
  const luminance = .2126 * channels[0] + .7152 * channels[1] + .0722 * channels[2];
  return (luminance + .05) / .05 >= 1.05 / (luminance + .05) ? '#000000' : '#ffffff';
}
