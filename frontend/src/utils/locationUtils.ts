// Utility functions for converting coordinates to human-readable addresses

export interface Location {
  lat: number;
  lng: number;
}

export interface LocationWithAddress extends Location {
  address: string;
}

/**
 * Convert coordinates to a human-readable address using Nominatim (OpenStreetMap)
 */
export async function getAddressFromCoordinates(lat: number, lng: number): Promise<string> {
  try {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`,
      {
        headers: {
          'User-Agent': 'VELOcabs App'
        }
      }
    );

    if (!response.ok) {
      throw new Error('Geocoding failed');
    }

    const data = await response.json();
    
    // Build a nice address from the components
    const address = data.address;
    const parts: string[] = [];

    // Add house number and road
    if (address.house_number) parts.push(address.house_number);
    if (address.road) parts.push(address.road);
    
    // Add neighbourhood or suburb
    if (address.neighbourhood) {
      parts.push(address.neighbourhood);
    } else if (address.suburb) {
      parts.push(address.suburb);
    }
    
    // Add city
    if (address.city) {
      parts.push(address.city);
    } else if (address.town) {
      parts.push(address.town);
    } else if (address.village) {
      parts.push(address.village);
    }

    // If we have a good address, return it
    if (parts.length > 0) {
      return parts.join(', ');
    }

    // Fallback to display_name if available
    if (data.display_name) {
      // Shorten the display name (take first 3-4 parts)
      const displayParts = data.display_name.split(', ').slice(0, 4);
      return displayParts.join(', ');
    }

    // Last resort: return coordinates
    return `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
  } catch (error) {
    console.error('Error getting address:', error);
    // Fallback to coordinates if geocoding fails
    return `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
  }
}

/**
 * Search for a location by name and return coordinates
 */
export async function getCoordinatesFromAddress(address: string): Promise<Location | null> {
  try {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}&limit=1`,
      {
        headers: {
          'User-Agent': 'VELOcabs App'
        }
      }
    );

    if (!response.ok) {
      throw new Error('Geocoding search failed');
    }

    const data = await response.json();
    
    if (data && data.length > 0) {
      return {
        lat: parseFloat(data[0].lat),
        lng: parseFloat(data[0].lon)
      };
    }

    return null;
  } catch (error) {
    console.error('Error searching for address:', error);
    return null;
  }
}

/**
 * Format a location string for display (shorten if too long)
 */
export function formatLocationForDisplay(location: string, maxLength: number = 50): string {
  if (location.length <= maxLength) {
    return location;
  }
  
  // If it's comma-separated, show first few parts
  const parts = location.split(', ');
  if (parts.length > 2) {
    return parts.slice(0, 2).join(', ') + '...';
  }
  
  // Otherwise just truncate
  return location.substring(0, maxLength - 3) + '...';
}