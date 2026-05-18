export const strictColors = {
  Food: "#0047cc",      
  Shopping: "#e6ce00",   
  Attractions: "#cc0000",
  Favourites: "#eb008b",  
  Music: "#800080",       
  Nature: "#009900",     
  
  CustomFallback: "#a855f7" 
};

export const formatLabel = (name, type) => {
  if (type === "tag") {
    return name.charAt(0).toUpperCase() + name.slice(1).toLowerCase();
  }
  return name; 
};