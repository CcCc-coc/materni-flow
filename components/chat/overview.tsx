import { motion } from "framer-motion";
import { dataset } from "@/lib/project";
import { getIcon } from "@/lib/icons";

export const Overview = () => {
  const { agent, chat } = dataset;

  return (
    <motion.div
      key="overview"
      className="max-w-3xl mx-auto md:mt-8"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      transition={{ delay: 0.3 }}
    >
      <div className="border border-slate-200 dark:border-slate-700 bg-white dark:bg-[#0F1D32] rounded-2xl shadow-sm">
        <div className="py-10 px-8">
          {/* Header */}
          <div className="flex flex-col items-center text-center mb-8">
            <h2 className="font-display text-2xl sm:text-3xl text-[#0A1628] dark:text-white mb-2">
              <span className="text-blue-600 dark:text-blue-400">{agent.name}</span>
            </h2>

            <p className="text-slate-500 dark:text-slate-400 max-w-md">
              {chat.welcomeSubtitle}
            </p>
          </div>

          {/* Quick Insight Cards - 2x2 Grid */}
          <div className="grid grid-cols-2 gap-4">
            {chat.insights.map((insight, index) => {
              const Icon = getIcon(insight.icon);
              return (
                <motion.div
                  key={insight.title}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 + index * 0.1 }}
                  className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-700/50"
                >
                  <Icon className="w-5 h-5 text-blue-600 dark:text-blue-400 mb-2" />
                  <h3 className="font-medium text-sm text-[#0A1628] dark:text-white">{insight.title}</h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{insight.description}</p>
                </motion.div>
              );
            })}
          </div>

          {/* Example prompts */}
          <div className="mt-6 pt-6 border-t border-slate-100 dark:border-slate-700">
            <p className="text-xs text-slate-400 dark:text-slate-500 text-center">
              {chat.tryExamples}
            </p>
          </div>
        </div>
      </div>
    </motion.div>
  );
};
