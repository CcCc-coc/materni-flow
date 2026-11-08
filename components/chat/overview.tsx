import { motion } from "framer-motion";

import CapabilityCard from "@/components/CapabilityCard";
import type { SiteConfig } from "@/lib/site/schema";

export const Overview = ({ site }: { site: SiteConfig }) => {
  const { chat, capabilities } = site;

  return (
    <motion.div
      key="overview"
      className="max-w-3xl mx-auto md:mt-8"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      transition={{ delay: 0.3 }}
    >
      <div className="border border-[#23445A] bg-[#0D263A] rounded-2xl shadow-[0_20px_60px_rgba(0,0,0,0.2)]">
        <div className="py-10 px-8">
          {/* Header */}
          <div className="flex flex-col items-center text-center mb-8">
            <h2 className="font-display text-2xl sm:text-3xl text-[#EAF7F6] mb-2">
              <span className="text-[#49D3C7]">{chat.agent}</span>
            </h2>

            <p className="text-[#8DAFC0] max-w-md">
              {chat.welcomeSubtitle}
            </p>
          </div>

          {/* The same four business threads the home page shows, from the same
              `[[capabilities]]`. Two arrays here is how the two screens drifted
              apart last time. */}
          <div className="grid grid-cols-2 gap-4">
            {capabilities.map((capability, index) => (
              <motion.div
                key={capability.title}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 + index * 0.1 }}
              >
                <CapabilityCard
                  capability={capability}
                  align={index % 2 === 0 ? "start" : "end"}
                  compact
                  className="h-full"
                />
              </motion.div>
            ))}
          </div>

          {/* Example prompts */}
          <div className="mt-6 pt-6 border-t border-[#23445A]">
            <p className="text-xs text-[#7295A7] text-center">
              {chat.tryExamples}
            </p>
          </div>
        </div>
      </div>
    </motion.div>
  );
};
