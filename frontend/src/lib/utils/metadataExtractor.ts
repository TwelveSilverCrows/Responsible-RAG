/**
 * Extracts Open Graph metadata from a URL via API route.
 * Returns partial source metadata that can be used to pre-populate the metadata form.
 */
export interface ExtractedMetadata {
  title: string | null;
  authors: string[];
  publicationDate: string | null;
  publisher: string | null;
  description: string | null;
  thumbnailUrl: string | null;
  language: string | null;
}

export async function extractMetadataFromUrl(url: string): Promise<ExtractedMetadata> {
  try {
    const response = await fetch(`/api/metadata?url=${encodeURIComponent(url)}`);
    if (!response.ok) {
      throw new Error('Failed to fetch metadata');
    }
    return await response.json();
  } catch {
    return {
      title: null,
      authors: [],
      publicationDate: null,
      publisher: null,
      description: null,
      thumbnailUrl: null,
      language: null,
    };
  }
}

/**
 * Validates YouTube URLs (supports youtu.be and full watch URLs)
 */
export function isValidYouTubeUrl(url: string): boolean {
  const patterns = [
    /^https?:\/\/(www\.)?youtube\.com\/watch\?v=[\w-]+/,
    /^https?:\/\/youtu\.be\/[\w-]+/,
    /^https?:\/\/(www\.)?youtube\.com\/embed\/[\w-]+/,
  ];
  return patterns.some((pattern) => pattern.test(url));
}

/**
 * Extracts YouTube video ID from a URL
 */
export function getYouTubeVideoId(url: string): string | null {
  const watchMatch = url.match(/[?&]v=([\w-]+)/);
  if (watchMatch) return watchMatch[1];
  const shortMatch = url.match(/youtu\.be\/([\w-]+)/);
  if (shortMatch) return shortMatch[1];
  const embedMatch = url.match(/youtube\.com\/embed\/([\w-]+)/);
  if (embedMatch) return embedMatch[1];
  return null;
}

/**
 * Generates a privacy-enhanced YouTube embed URL
 */
export function getYouTubeEmbedUrl(videoId: string): string {
  return `https://www.youtube-nocookie.com/embed/${videoId}`;
}

/**
 * Generates a YouTube thumbnail URL from video ID
 */
export function getYouTubeThumbnail(videoId: string): string {
  return `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`;
}
