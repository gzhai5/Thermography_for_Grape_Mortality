# Load the glmmTMB package
library(glmmTMB)
library(emmeans)
library(ggplot2)
library(plotly)
library(ggpubr)
library(gridExtra)
library(grid)

base_font_size <- 18
cultivar_map <- list(
  "CF" = "Cabernet Franc",
  "CON" = "Concord",
  "PN" = "Pinot Noir",
  "RIES" = "Riesling"
)
map_cultivar <- function(df) {
  df$cultivar <- sapply(df$cultivar, function(x) cultivar_map[[x]])
  return(df)
}
feature_labels <- list(
  "peak_temperature" = "Peak Temperature",
  "rising_waveform_feature" = "Rising Waveform Feature",
  "falling_waveform_feature" = "Falling Waveform Feature",
  "pca_0" = "PC 0",
  "pca_1" = "PC 1",
  "pca_2" = "PC 2"
)

# Load your data
data <- read.csv("/Users/mud/Desktop/Thermography_for_Grape_Mortality/code/data_analysis/statistics/csv/stat_all_data_noabnormal_extend_mean_normalization_pca_round_6.csv")

data$treatment <- as.factor(data$treatment)
data$cultivar <- as.factor(data$cultivar)
data$dev_stage <- as.factor(data$dev_stage)
data$mortality <- as.factor(data$mortality)
data$segment <- as.factor(data$segment)
data$starting_temperature <- as.numeric(data$starting_temperature)
data$peak_temperature <- as.numeric(data$peak_temperature)
data$rising_waveform_feature <- as.numeric(data$rising_waveform_feature)
data$falling_waveform_feature <- as.numeric(data$falling_waveform_feature)
data$rising_waveform_std <- as.numeric(data$rising_waveform_std)
data$falling_waveform_std <- as.numeric(data$falling_waveform_std)
data$cane2 <- as.factor(paste0(data$cultivar, "_", data$dev_stage, "_", data$cane))

data$pca_0 <- as.numeric(data$pca_0)
data$pca_1 <- as.numeric(data$pca_1)
data$pca_2 <- as.numeric(data$pca_2)

# Visualize distributions
hist(data$starting_temperature, main="Distribution of Starting Tempature", xlab="Starting Tempature", breaks=30)
hist(data$peak_temperature, main="Distribution of Peak Tempature", xlab="Peak Tempature", breaks=30)
hist(data$rising_waveform_feature, main="Distribution of Rising Waveform Feature", xlab="Rising Waveform Feature", breaks=30)
hist(data$rising_waveform_std, main="Distribution of Rising Waveform Std", xlab="Rising Waveform Std", breaks=30)
hist(data$falling_waveform_feature, main="Distribution of Falling Waveform Feature", xlab="Falling Waveform Feature", breaks=30)
hist(data$falling_waveform_std, main="Distribution of Falling Waveform Stde", xlab="Falling Waveform Std", breaks=30)


# ---- Development Stage 6 ----
cat("Running Gamma model for Development Stage 6...\n")
stage_6_data <- data[data$dev_stage == "6", ]

# Apply filtering to exclude specified conditions
stage_6_data <- stage_6_data[!(stage_6_data$treatment == 1 & stage_6_data$mortality == "false") &
                               !(stage_6_data$treatment == 6), ]

results <- list()
plot_list <- list()

# Define features to analyze
features <- c("peak_temperature", "rising_waveform_feature", "falling_waveform_feature", 
              "pca_0", "pca_1", "pca_2")


for (feature in features) {
  # Model with feature as the dependent variable
  model <- glmmTMB(
    as.formula(paste(feature, "~ cultivar * mortality + (1 | segment)")),
    data = stage_6_data,
    family = gaussian()
  )
  
  # Summary of the model
  cat("Results for feature:", feature, "\n")
  print(summary(model))
  
  # Comprehensive pairwise comparisons
  emm <- emmeans(model, ~ cultivar * mortality)
  pairwise_results <- pairs(emm, adjust = "bonferroni")  # Adjust for multiple comparisons
  results[[feature]] <- as.data.frame(pairwise_results)
  
  # Transform emmeans values and confidence intervals back to original scale
  emm_df <- as.data.frame(emm)
  emm_df <- map_cultivar(emm_df)
  emm_df$mortality <- as.logical(emm_df$mortality)
  emm_df$mortality <- ifelse(emm_df$mortality, "Viable", "Non-Viable")
  
  # Plotting
  p <- ggplot(emm_df, aes(x = mortality, y = emmean, color = cultivar, group = cultivar)) +
    geom_line(linewidth = 0.3) +
    geom_point(size = 2) +
    geom_errorbar(aes(ymin = lower.CL, ymax = upper.CL), width = 0.2) +
    labs(x = NULL, y = feature_labels[[feature]]) +
    theme_minimal(base_size = base_font_size) +
    theme(
      plot.title = element_blank(),  # Remove title
      axis.title = element_text(size = base_font_size),
      axis.text = element_text(size = base_font_size - 2),
      legend.title = element_blank(),  # Remove legend title
      legend.text = element_text(size = base_font_size - 2),
    )
  
  # Append the plot to the list
  plot_list[[feature]] <- p
}

# Combine all plots into a 2x3 grid
combined_plot <- ggarrange(
  plot_list[["peak_temperature"]], 
  plot_list[["rising_waveform_feature"]],
  plot_list[["falling_waveform_feature"]],
  plot_list[["pca_0"]], 
  plot_list[["pca_1"]],
  plot_list[["pca_2"]],
  ncol = 3, nrow = 2, 
  common.legend = TRUE, legend = "bottom"
)

# Save the combined figure
ggsave("/Users/mud/Desktop/Thermography_for_Grape_Mortality/code/data_analysis/paper/glme/glme_exp5.svg", 
       plot=combined_plot, width = 14, height = 8)
dev.off()

# Display the combined plot
print(combined_plot)

