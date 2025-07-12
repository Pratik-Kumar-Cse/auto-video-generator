import json
from ..llm.llm_call import divide_and_get_search_terms

from ..serper import images_search, video_search


def generate_video_data(script):

    scenes = divide_and_get_search_terms(script)

    print(scenes)

    for scene in json.loads(scenes):
        search_terms = scene.get("search_terms")
        images = images_search(search_terms, num=5)
        video = video_search(search_terms, num=5)

        print(images, video)


# generate_video_data(
#     """
#     AI vs. Blockchain: Discover the Game-Changing Technologies Taking Over!"

#     #### [INTRO]
#     [Opening shot: Futuristic cityscape with AI and blockchain symbols weaving in and out]

#     **[Narrator - Male AI Researcher]:**
#     *Hey there, tech enthusiasts! Today, we’re diving deep into the latest groundbreaking trends in AI and Blockchain that are shaking up the tech world. If you’re somewhere between 20 and 45, you really won't want to miss this — these advancements are about to, like, change everything! Let's jump right in!*

#     #### [SECTION 1: GENERATIVE AI TAKEOVER]
#     [Cut to: Office environment with AI-powered customer service bots]

#     **[Narrator]:**
#     *Alright, so first up, let's chat about generative AI in customer care. Get this — an incredible 80% of organizations are either investing or planning to invest in generative AI. And, um, with 57% expecting increased call volumes pretty soon, companies are all in on tech upgrades, operational efficiency, and, you know, employee upskilling.*

#     [Visual: Stats and a quick demo of an AI chatbot in action]

#     **[Example - Amazon]:**
#     *Take Amazon, for example. They’ve totally revolutionized customer service with AI. Virtual assistants handle inquiries super quickly and efficiently, cutting costs and, like, really enhancing customer satisfaction.*

#     #### [SECTION 2: AI IN CYBERSECURITY AND FINANCE]
#     [Cut to: Banks and digital security locks interchanging]

#     **[Narrator]:**
#     *Now, let’s talk about AI in financial services, where cybersecurity is, uh, more critical than ever. Despite adopting cloud computing and AI rapidly, 70% of financial institutions think they’re underspending on cybersecurity — can you believe it?*

#     [Visual: Alarm bells and lock icons, stats display]

#     **[Example - JPMorgan Chase]:**
#     *JPMorgan Chase, however, is on top of this by integrating AI with robust security measures — really setting a gold standard to ensure innovation doesn’t compromise security.*

#     #### [SECTION 3: AI IN TRADITIONAL INDUSTRIES]
#     [Cut to: Trains and railways augmented with AI tech]

#     **[Narrator]:**
#     *Moving on, AI in the railway industry is, um, pretty mind-blowing. It could potentially unlock up to $22 billion in annual value. But only 25% of rail companies have adopted AI at scale. Like, what’s holding the rest back?*

#     [Visual: Animated trains, predictive maintenance in action]

#     **[Example - Deutsche Bahn]:**
#     *Deutsche Bahn is a frontrunner here, using AI for predictive maintenance and shift optimization. They’ve cut downtimes drastically and improved service reliability. Really impressive stuff!*

#     #### [TRANSITION TO BLOCKCHAIN]
#     [Transition: Digital "atom" particles morphing into blockchain and cryptocurrency logos]

#     **[Narrator]:**
#     *And now... let's shift gears to the dynamic world of blockchain.*

#     #### [SECTION 4: CRYPTOCURRENCY SURGES AND INSTITUTIONAL INTEREST]
#     [Cut to: Rising cryptocurrency graphs and institutional buildings]

#     **[Narrator]:**
#     *Last week was wild for cryptocurrency, with Bitcoin spiking 22%! This surge came from political turbulence and speculation about, like, a more crypto-friendly regulatory environment in the near future.*

#     [Visual: Interactive Bitcoin chart, news snippets]

#     **[Example - Marathon Digital]:**
#     *Marathon Digital is diversifying big time by investing in Kaspa mining. They expect to control a whopping 16% of Kaspa’s global hashrate! Clearly, institutions are, like, seriously moving towards emerging blockchain technologies.*

#     #### [SECTION 5: DEFI DEVELOPMENTS AND TOKEN INNOVATIONS]
#     [Cut to: Decentralized finance (DeFi) landscapes and token generation animations]

#     **[Narrator]:**
#     *In the world of DeFi, MakerDAO’s Spark Tokenization Grand Prix is aiming to invest $1 billion into real-world assets. Major players like BlackRock are getting involved, which is a really strong signal of the growing synergy between traditional finance and decentralized platforms.*

#     [Visual: Token minting, DeFi platforms in operation]

#     **[Example - Shiba Inu]:**
#     *And get this, Shiba Inu raised $12 million by selling TREAT tokens. They're funding a blockchain focused on enhancing transaction privacy. This kind of innovation shows how meme coins are expanding into more sophisticated applications. Pretty cool, huh?*

#     #### [SECTION 6: BLOCKCHAIN INTEGRATION AND GROWTH]
#     [Cut to: Telegram logo and blockchain integration demonstrations]

#     **[Narrator]:**
#     *Toncoin is thriving thanks to its integration with Telegram. They’re launching an in-app decentralized store and Web3 browser. Like, the potential user adoption here looks massive, given Telegram’s huge user base.*

#     [Visual: Telegram integration, Web3 browser demo]

#     **[Example - Cardano]:**
#     *Meanwhile, Cardano’s gearing up for a major upgrade with the Node 9.0 update. This introduces decentralized governance model — the buzz has already pushed ADA’s price up by 26%!*

#     #### [OUTRO]
#     [Closing shot: AI and blockchain symbols intertwine into a digital handshake]

#     **[Narrator]:**
#     *From AI revolutionizing customer service and financial security to blockchain’s explosive growth and innovative integrations, these leading technologies are crafting the future. So, stay tuned, tech enthusiasts, because the future is not just near — it’s happening now!*

#     **[Narrator continues with enthusiasm]:**
#     *And hey, now I want to hear from you! Which of these technologies do you find most exciting? Have you seen any real-world applications of AI or blockchain that just blew your mind? Drop your thoughts in the comments below!*

#     **[Narrator]:**
#     *If you liked this video, make sure to give it a thumbs up, subscribe to our channel, and hit that notification bell so you never miss an update. Let’s keep this conversation going, and I’ll see you in the next video!*
#     """
# )
