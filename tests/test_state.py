import unittest
import numpy as np

from qsi.state import State, StateProp

class TestStateReorder(unittest.TestCase):
    def setUp(self):
        # Create StateProp instances
        self.state_prop_A = StateProp(state_type="light", truncation=2, wavelength=700, polarization="R", uuid="A")
        self.state_prop_B = StateProp(state_type="internal", truncation=3, uuid="B")
        self.state_prop_C = StateProp(state_type="internal", truncation=4, uuid="C")
        self.state_prop_D = StateProp(state_type="light", truncation=2, wavelength=800, polarization="L", uuid="D")
        
        # Create State instances
        self.state_A = State(self.state_prop_A)
        self.state_A.state[0,0] = 0
        self.state_A.state[1,1] = 1
        self.state_B = State(self.state_prop_B)
        self.state_C = State(self.state_prop_C)
        self.state_D = State(self.state_prop_D)
        self.state_D.state[0,0] = 0
        self.state_D.state[1,1] = 1
        
        # Join states to create a product space
        self.state_A.join(self.state_B)
        self.state_A.join(self.state_C)
        self.state_A.join(self.state_D)


    def test_simple_reorder(self):
        pA = StateProp(state_type="light", truncation=2, wavelength=700, polarization="R", uuid="A")
        pB = StateProp(state_type="internal", truncation=3, uuid="B")

        A = State(pA)
        A.state[0,0] = 0
        A.state[1,1] = 1
        B = State(pB)
        A.join(B)
        A._reorder([pB, pA])

        self.assertEqual(A.state[1,1],1)
        expected_order = [pB.uuid, pA.uuid]
        actual_order = [prop.uuid for prop in A.state_props]
        self.assertEqual(expected_order, actual_order)


class TestKrausOperatorApply(unittest.TestCase):

    def test_identity_kraus_operators(self):
        pA = StateProp(state_type="light", truncation=2, wavelength=700, polarization="R")
        pB = StateProp(state_type="internal", truncation=3)

        A = State(pA)
        A.state[0,0] = 0
        A.state[1,1] = 1
        B = State(pB)
        A.join(B)
        original_state = A.state.copy()
        A.apply_kraus_operators([np.eye(pA.truncation)],[pA])
        np.testing.assert_array_equal(original_state, A.state)


    def test_X_kraus_operator(self):
        pA = StateProp(state_type="light", truncation=2, wavelength=700, polarization="R")
        pB = StateProp(state_type="internal", truncation=3)

        test_state = np.zeros((6,6))
        test_state[0,0] = 1

        A = State(pA)
        B = State(pB)

        A.join(B)
        np.testing.assert_array_equal(test_state, A.state)
        op1 = np.array([[0,1],[1,0]])
        A.apply_kraus_operators([op1], [pA])
        expected_state = np.kron(
            np.array([[0,0],[0,1]]),
            np.array([[1,0,0],[0,0,0],[0,0,0]]),
        )
        np.testing.assert_array_equal(expected_state, A.state)



class TestStateReduction(unittest.TestCase):

    def test_simple_reduction(self):
        pA = StateProp(state_type="light", truncation=2, wavelength=700, polarization="R")
        pB = StateProp(state_type="internal", truncation=3)

        test_state = np.zeros((6,6))
        test_state[0,0] = 1

        A = State(pA)
        B = State(pB)

        A.join(B)
        state = A.get_reduced_state([pA])
        print("REDUCTION")
        print(state)
        print(A.state)


if __name__ == "__main__":
    unittest.main()
