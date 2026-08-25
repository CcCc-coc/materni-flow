import { Metadata } from "next"
import { generateSEOMetadata } from "@/lib/seo/generateMetadata"
import { METADATA } from "@/lib/constants"
import { loadBusinessContext, loadSite } from "@/lib/site/load"
import HomePageContent from "./HomePageContent"


export async function generateMetadata(): Promise<Metadata> {
  return generateSEOMetadata({
    title: METADATA.TITLE,
    description: METADATA.DESCRIPTION,
    keywords: [...METADATA.KEYWORDS],
    url: "",
    ogTitle: METADATA.TITLE,
    ogDescription: METADATA.DESCRIPTION,
    imageAlt: METADATA.TITLE,
    twitterTitle: METADATA.TITLE,
    twitterDescription: METADATA.DESCRIPTION,
  })
}

export default function HomePage() {
  return <HomePageContent site={loadSite()} businessContext={loadBusinessContext()} />
}
