import mesa
import random
import matplotlib.pyplot as plt


class StudentAgent(mesa.Agent):
    def __init__(self, unique_id, model, name, personality, interests, academic_performance, social_status):
        super().__init__(unique_id, model)
        self.name = name
        self.personality = personality
        self.interests = interests
        self.academic_performance = academic_performance
        self.social_status = social_status

    def interact_with_agent(self, other_agent):
        # Determine the likelihood of a positive interaction based on the similarity of the students' attributes
        similarity = self.similarity(other_agent)
        likelihood_of_positive_interaction = similarity * 0.5 + random.random() * 0.5

        # Determine the outcome of the interaction
        if random.random() < likelihood_of_positive_interaction:
            # Positive interaction
            self.social_status += 1
            other_agent.social_status += 1
        else:
            # Negative interaction
            self.social_status -= 1
            other_agent.social_status -= 1

    def similarity(self, other_agent):
        # Calculate the similarity of the students' attributes
        personality_similarity = self.personality == other_agent.personality
        interests_similarity = self.interests == other_agent.interests
        academic_performance_similarity = abs(
            self.academic_performance - other_agent.academic_performance) <= 1

        similarity = personality_similarity * 0.3 + interests_similarity * \
            0.4 + academic_performance_similarity * 0.3

        return similarity


class SocialGrid(mesa.Model):
    def __init__(self, num_agents):
        super().__init__()
        self.num_agents = num_agents

        # Create a list of agents
        self.agents = []

        # Create a MultiGrid to represent the classroom
        self.grid = mesa.space.MultiGrid(num_agents, num_agents, True)

        # Place the agents on the grid
        for i in range(num_agents):
            for j in range(num_agents):
                if i + j < num_agents:
                    agent = StudentAgent(unique_id=i + j, model=self, name=f"Student {i + j}", personality=random.choice(["introverted", "extroverted", "ambivert"]), interests=[
                                         "reading", "drawing", "sports", "gaming", "music", "dance"], academic_performance=random.randint(60, 100), social_status=random.randint(0, 5))
                    self.grid.place_agent(agent, (i, j))
                    self.agents.append(agent)

    def step(self):
        # Shuffle the agents to ensure that they interact with different students each step
        random.shuffle(self.agents)

        # Have each agent interact with a random number of other agents
        for agent in self.agents:
            num_interactions = random.randint(1, 3)
            for _ in range(num_interactions):
                other_agent = random.choice(self.agents)
                if agent != other_agent:
                    agent.interact_with_agent(other_agent)

    def visualize_social_relationships(self):
        # Create a matrix to represent the social relationships between the students
        social_relationships = [
            [0 for _ in range(len(self.agents))] for _ in range(len(self.agents))]

        # Update the social relationships matrix based on the social status of each student
        for i, agent1 in enumerate(self.agents):
            for j, agent2 in enumerate(self.agents):
                social_relationships[i][j] = agent1.social_status if i != j else 0

        # Create a plot to visualize the social relationships matrix
        plt.matshow(social_relationships)
        plt.colorbar()
        plt.title("Social Relationships Matrix")

        # Add labels for each student
        for i, student in enumerate(self.agents):
            plt.annotate(student.name, (i, len(self.agents) -
                         i - 1), ha='center', va='center')

        plt.show()


def main():
    # Create a model with 100 agents
    model = SocialGrid(100)

    # Run the model for 100 steps
    for _ in range(100):
        model.step()

    model.visualize_social_relationships()


if __name__ == "__main__":
    main()
