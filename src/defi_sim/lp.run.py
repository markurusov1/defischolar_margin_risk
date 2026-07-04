from aave.aave_original import AaveSimulator
from uniswap.il_v3 import UniswapV3Position

# A simple test of Aave Lending and Uniswap Impermanent Loss calculation

if __name__ == "__main__":
    #Starting with this funding:
    initial_eth_max = 3000.0
    initial_usdc_max = 2000.0
    print(f"Initial ETH/USDC funds: {initial_eth_max:.2f} ETH / {initial_usdc_max:.2f} USDC")

    #Create a position in a V3 Uniswap pool
    position = UniswapV3Position("1234",
        initial_eth_max,
        initial_usdc_max,
        range_width=0.1 #this is the concentrated liquidity range in the pool width (±10% here)
    )
    #Get position value at the initial price
    position_value = position.compute_position_value(position.initial_price)
    print(f"\nPool position value at initial price: {position_value:.2f} USDC")

    #Create an Aave Lender
    aaveLender = AaveSimulator()

    #Compute loan amount
    loan_amount = aaveLender.borrow(position_value)
    print(f"Loan amount: {loan_amount:.2f} USDC")

    #Check with the lender
    lenderResponse = aaveLender.decide_liquidation(position_value, loan_amount)
    print(f"Lender response: {lenderResponse}")

    # Simulate a 10% price drop
    price_drop = 0.10
    new_price = position.initial_price * (1 - price_drop)
    print(f"\nAfter {price_drop * 100:.0f}% ETH price drop:")
    print(f"New price (USDC per ETH): {new_price:.4f}")

    position_value = position.compute_position_value(new_price)
    print(f"Pool position value at new price: {position_value:.2f} USDC")

    hold_value = position.compute_hold_value(new_price)
    print(f"Hold strategy value at new price: {hold_value:.2f} USDC")

    il = position.compute_impermanent_loss(new_price)
    print(f"Impermanent Loss: {il:.4f} or {il * 100:.2f}%")

    lenderResponse = aaveLender.decide_liquidation(position_value, loan_amount)
    print(f"Lender response: {lenderResponse}")