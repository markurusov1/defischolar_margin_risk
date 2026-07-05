import math

class UniswapV3Position:
    """
    A class to model a Uniswap v3 concentrated liquidity position for ETH/USDC.

    This allows setting up the position with initial max deposits and range width,
    then computing the position's value at any given price (e.g., for use as collateral in Aave).
    """

    def __init__(self, id:str, initial_eth_max: float, initial_usdc_max: float, range_width: float):
        """
        Initialize the position.

        Args:
            position id
            initial_eth_max: Maximum ETH to deposit.
            initial_usdc_max: Maximum USDC to deposit.
            range_width: Fractional width for the price range (e.g., 0.1 for ±10%).
        """
        self.position_id=id
        if range_width <= 0 or range_width >= 1:
            raise ValueError("Range width should be between 0 and 1 (exclusive).")

        # Initial price (USDC per ETH) implied by max deposits
        self.initial_price = initial_usdc_max / initial_eth_max

        # Concentrated price range
        self.lower_price = self.initial_price * (1 - range_width)
        self.upper_price = self.initial_price * (1 + range_width)

        # Sqrt values for efficiency
        self.sqrt_initial = math.sqrt(self.initial_price)
        self.sqrt_lower = math.sqrt(self.lower_price)
        self.sqrt_upper = math.sqrt(self.upper_price)

        # Calculate liquidity L based on min that fits the range
        delta0 = 1 / self.sqrt_initial - 1 / self.sqrt_upper
        delta1 = self.sqrt_initial - self.sqrt_lower
        L0 = initial_eth_max / delta0 if delta0 > 0 else float('inf')
        L1 = initial_usdc_max / delta1 if delta1 > 0 else float('inf')
        self.liquidity = min(L0, L1)

        # Actual deposited amounts at initial price
        self.actual_eth, self.actual_usdc = self.get_amounts(self.initial_price)

        """ print(f"\nPosition {self.position_id}:")
        print(f"Initial price (USDC per ETH): {self.initial_price:.4f}")
        print(f"Lower bound of range: {self.lower_price:.4f}")
        print(f"Upper bound of range: {self.upper_price:.4f}")
        print(f"Actual ETH deposited: {self.actual_eth:.2f} (excess returned: {initial_eth_max - self.actual_eth:.2f})")
        print(f"Actual USDC deposited: {self.actual_usdc:.2f} (excess returned: {initial_usdc_max - self.actual_usdc:.2f})")
        print(f"Initial LP position value: {self.compute_position_value(self.initial_price):.2f} USDC")
        """
    def get_amounts(self, current_price: float) -> tuple[float, float]:
        """
        # Compute how much of ETH and USDC are actually inside the concentrated liquidity position
        Args:
            current_price: Current price (USDC per ETH).
        Returns:
            (amount_eth, amount_usdc)
        """
        if current_price <= self.lower_price:
            amount_eth = self.liquidity * (1 / self.sqrt_lower - 1 / self.sqrt_upper)
            amount_usdc = 0
        elif current_price >= self.upper_price:
            amount_eth = 0
            amount_usdc = self.liquidity * (self.sqrt_upper - self.sqrt_lower)
        else:
            sqrt_current = math.sqrt(current_price)
            amount_eth = self.liquidity * (1 / sqrt_current - 1 / self.sqrt_upper)
            amount_usdc = self.liquidity * (sqrt_current - self.sqrt_lower)
        return amount_eth, amount_usdc

    def compute_position_value(self, current_price: float) -> float:
        """
        Compute the value of the LP position at the given current price, in USDC.
        This can be fed as collateral value to Aave simulations.
        Args:
            current_price: Current price (USDC per ETH).
        Returns:
            Position value in USDC.
        """
        amount_eth, amount_usdc = self.get_amounts(current_price)
        return amount_eth * current_price + amount_usdc

    def compute_hold_value(self, current_price: float) -> float:
        """
        Compute the value if the actual deposited tokens were simply held (for IL comparison).
        Args:
            current_price: Current price (USDC per ETH).
        Returns:
            Hold value in USDC.
        """
        return self.actual_eth * current_price + self.actual_usdc

    def compute_impermanent_loss(self, current_price: float) -> float:
        """
        Compute impermanent loss at the given price.
        Returns:
            IL as a decimal (negative = loss).
        """
        position_value = self.compute_position_value(current_price)
        hold_value = self.compute_hold_value(current_price)
        return (position_value / hold_value) - 1 if hold_value != 0 else 0
