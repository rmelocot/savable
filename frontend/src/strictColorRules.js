// A strict color map enforcing the "carbon copy" rule
// from your Figma/images.
export const strictColors = {
  Food: "#0047cc",        // Bright blue from image_5.png
  Shopping: "#e6ce00",    // Solid yellow from image_7.png
  Attractions: "#cc0000", // Bright red from image_7.png
  Favourites: "#eb008b",  // Pink from image_7.png
  Music: "#800080",       // Purple from image_7.png
  Nature: "#009900",      // Green from image_7.png
  
  // Custom User Folders (as defined in your discover page, like "SANJAY")
  CustomFallback: "#a855f7" // Brands standard custom color
};

// Ensures proper capitalization or uppercase based on your images
export const formatLabel = (name, type) => {
  if (type === "tag") {
    // Labels on tags (like image_5.png) are capitalized: "Food"
    return name.charAt(0).toUpperCase() + name.slice(1).toLowerCase();
  }
  // This is a fallback; based on your image, "SANJAY" is user-generated 
  // and keeps its input casing. But we handle default "Food" as capitalized.
  return name; 
};